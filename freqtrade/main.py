#!/usr/bin/env python3
import copy
import json
import logging
import sys
import time
import traceback
from datetime import datetime
from typing import Dict, List, Optional

import arrow
import requests
from cachetools import cached, TTLCache

from freqtrade import (DependencyException, OperationalException, TradeException,
                       __version__, exchange, persistence, rpc)
from freqtrade.analyze import get_signal
from freqtrade.fiat_convert import CryptoToFiatConverter
from freqtrade.misc import (State, get_state, load_config, parse_args,
                            throttle, update_state, DEFAULT_STRATEGY)
from freqtrade.persistence import Trade
from freqtrade.watchdog import Watchdog
from freqtrade.strategy.strategy import Strategy

logger = logging.getLogger('freqtrade')

_CONF = {}
_BLACKLIST = set()


def refresh_whitelist(whitelist: List[str]) -> List[str]:
    """
    Check wallet health and remove pair from whitelist if necessary
    :param whitelist: the sorted list (based on BaseVolume) of pairs the user might want to trade
    :return: the list of pairs the user wants to trade without the one unavailable or black_listed
    """
    sanitized_whitelist = whitelist
    health = exchange.get_wallet_health()
    known_pairs = set()
    for status in health:
        pair = '{}_{}'.format(_CONF['stake_currency'], status['Currency'])
        # pair is not int the generated dynamic market, or in the blacklist ... ignore it
        if pair not in whitelist or pair in _CONF['exchange'].get('pair_blacklist', []):
            continue
        # else the pair is valid
        known_pairs.add(pair)
        # Market is not active
        if not status['IsActive']:
            sanitized_whitelist.remove(pair)
            logger.debug(
                'Ignoring %s from whitelist (reason: %s).',
                pair, status.get('Notice') or 'wallet is not active'
            )

    # We need to remove pairs that are unknown
    final_list = [x for x in sanitized_whitelist if x in known_pairs]
    return final_list


def _process(nb_assets: Optional[int] = 0, strategy: Optional[str] = DEFAULT_STRATEGY) -> bool:
    """
    Queries the persistence layer for open trades and handles them,
    otherwise a new trade is created.
    :param: nb_assets: the maximum number of pairs to be traded at the same time
    :return: True if a trade has been created or closed, False otherwise
    """
    state_changed = False
    try:
        # Refresh whitelist based on wallet maintenance
        sanitized_list = refresh_whitelist(
            gen_pair_whitelist(
                _CONF['stake_currency'], nb_assets=nb_assets
            ) if nb_assets else _CONF['exchange']['pair_whitelist']
        )

        # Keep only the subsets of pairs wanted (up to nb_assets)
        final_list = sanitized_list[:nb_assets] if nb_assets else sanitized_list
        _CONF['exchange']['pair_whitelist'] = final_list

        # Query trades from persistence layer
        trades = Trade.query.filter(Trade.is_open.is_(True)).all()
        if len(trades) < _CONF['max_open_trades']:
            try:
                # Create entity and execute trade
                state_changed = create_trade(float(_CONF['stake_amount']), strategy)
                if not state_changed:
                    logger.debug(
                        'Checked all whitelisted currencies. '
                        'Found no suitable entry positions for buying. Will keep looking ...'
                    )
            except DependencyException as exception:
                logger.warning('Unable to create trade: %s', exception)

        for trade in trades:
            # Get order details for actual price per unit
            if trade.open_order_id:
                # Update trade with order values
                logger.info('Got open order for %s', trade)
                trade.update(exchange.get_order(trade.open_order_id))

            if trade.is_open and trade.open_order_id is None:
                # Check if we can sell our current pair
                state_changed = handle_trade(trade, strategy) or state_changed

        if 'unfilledtimeout' in _CONF:
            # Check and handle any timed out open orders
            check_handle_timedout(_CONF['unfilledtimeout'])

            Trade.session.flush()

    except (requests.exceptions.RequestException, json.JSONDecodeError) as error:
        logger.warning(
            'Got %s in _process(), retrying in 30 seconds...',
            error
        )
        time.sleep(30)

    except OperationalException as ex:
        logger.exception('Got OperationalException')
        rpc.send_msg('*Status:* Got OperationalException:\n```\n{traceback}```{hint}'.format(
            traceback=traceback.format_exc(),
            hint='Issue `/start` if you think it is safe to restart.'
        ))
        logger.info('Stopping trader ...')
        update_state(State.STOPPED)

    return state_changed


def check_handle_timedout(timeoutvalue: int) -> None:
    """
    Check if any orders are timed out and cancel if neccessary
    :param timeoutvalue: Number of minutes until order is considered timed out
    :return: None
    """
    timeoutthreashold = arrow.utcnow().shift(minutes=-timeoutvalue).datetime

    for trade in Trade.query.filter(Trade.open_order_id.isnot(None)).all():
        try:
            order = exchange.get_order(trade.open_order_id)
            ordertime = arrow.get(order['opened'])
            logger.info("Compare order time {} and {}".format(ordertime, timeoutthreashold))
            if order['type'] == "LIMIT_BUY" and ordertime < timeoutthreashold:
                # Buy timeout - cancel order
                exchange.cancel_order(trade.open_order_id)
                if order['remaining'] == order['amount']:
                    # if trade is not partially completed, just delete the trade
                    Trade.session.delete(trade)
                    Trade.session.flush()
                    logger.info('Buy order timeout for %s.', trade)
                    rpc.send_msg('*Timeout:* Unfilled buy order for {} cancelled'.format(
                                 trade.pair.replace('_', '/')))
                else:
                    # if trade is partially complete, edit the stake details for the trade
                    # and close the order
                    trade.amount = order['amount'] - order['remaining']
                    trade.stake_amount = trade.amount * trade.open_rate
                    trade.open_order_id = None
                    logger.info('Partial buy order timeout for %s.', trade)
                    rpc.send_msg('*Timeout:* Remaining buy order for {} cancelled'.format(
                                 trade.pair.replace('_', '/')))
            elif order['type'] == "LIMIT_SELL" and ordertime < timeoutthreashold:
                # Sell timeout - cancel order and update trade
                if order['remaining'] == order['amount']:
                    # if trade is not partially completed, just cancel the trade
                    exchange.cancel_order(trade.open_order_id)
                    trade.close_rate = None
                    trade.close_profit = None
                    trade.close_date = None
                    trade.is_open = True
                    trade.open_order_id = None
                    logger.info('Sell order timeout for %s.', trade)
                    rpc.send_msg('*Timeout:* Unfilled sell order for {} cancelled'.format(
                                 trade.pair.replace('_', '/')))
                    return True
                else:
                    # TODO: figure out how to handle partially complete sell orders
                    pass
        except TradeException as e:
            logger.warning('Error in order timeout check: {}'.format(e))


def execute_sell(trade: Trade, limit: float) -> None:
    """
    Executes a limit sell for the given trade and limit
    :param trade: Trade instance
    :param limit: limit rate for the sell order
    :return: None
    """
    # Execute sell and update trade record
    order_id = exchange.sell(str(trade.pair), limit, trade.amount)
    trade.open_order_id = order_id

    fmt_exp_profit = round(trade.calc_profit_percent(rate=limit) * 100, 2)
    profit_trade = trade.calc_profit(rate=limit)

    message = '*{exchange}:* Selling [{pair}]({pair_url}) with limit `{limit:.8f}`'.format(
        exchange=trade.exchange,
        pair=trade.pair.replace('_', '/'),
        pair_url=exchange.get_pair_detail_url(trade.pair),
        limit=limit
    )

    # For regular case, when the configuration exists
    if 'stake_currency' in _CONF and 'fiat_display_currency' in _CONF:
        fiat_converter = CryptoToFiatConverter()
        profit_fiat = fiat_converter.convert_amount(
            profit_trade,
            _CONF['stake_currency'],
            _CONF['fiat_display_currency']
        )
        message += '` ({gain}: {profit_percent:.2f}%, {profit_coin:.8f} {coin}`' \
                   '` / {profit_fiat:.3f} {fiat})`'.format(
                       gain="profit" if fmt_exp_profit > 0 else "loss",
                       profit_percent=fmt_exp_profit,
                       profit_coin=profit_trade,
                       coin=_CONF['stake_currency'],
                       profit_fiat=profit_fiat,
                       fiat=_CONF['fiat_display_currency'],
                   )
    # Because telegram._forcesell does not have the configuration
    # Ignore the FIAT value and does not show the stake_currency as well
    else:
        message += '` ({gain}: {profit_percent:.2f}%, {profit_coin:.8f})`'.format(
            gain="profit" if fmt_exp_profit > 0 else "loss",
            profit_percent=fmt_exp_profit,
            profit_coin=profit_trade
        )

    # Send the message
    rpc.send_msg(message)
    Trade.session.flush()


def min_roi_reached(trade: Trade, current_rate: float, current_time: datetime, strategy: str) -> bool:
    """
    Based an earlier trade and current price and ROI configuration, decides whether bot should sell
    :return True if bot should sell at current rate
    """
    strategy = Strategy(strategy)

    current_profit = trade.calc_profit_percent(current_rate)
    if strategy.stoploss is not None and current_profit < float(strategy.stoploss):
        logger.debug('Stop loss hit.')
        return True

    # Check if time matches and current rate is above threshold
    time_diff = (current_time - trade.open_date).total_seconds() / 60
    for duration, threshold in sorted(strategy.minimal_roi.items()):
        if time_diff > float(duration) and current_profit > threshold:
            return True

    logger.debug('Threshold not reached. (cur_profit: %1.2f%%)', float(current_profit) * 100.0)
    return False


def handle_trade(trade: Trade, strategy: str) -> bool:
    """
    Sells the current pair if the threshold is reached and updates the trade record.
    :return: True if trade has been sold, False otherwise
    """
    if not trade.is_open:
        raise ValueError('attempt to handle closed trade: {}'.format(trade))

    logger.debug('Handling %s ...', trade)
    current_rate = exchange.get_ticker(trade.pair)['bid']

    (buy, sell) = (False, False)

    if _CONF.get('experimental', {}).get('use_sell_signal'):
        (buy, sell) = get_signal(trade.pair, strategy)

    # Check if minimal roi has been reached and no longer in buy conditions (avoiding a fee)
    if not buy and min_roi_reached(trade, current_rate, datetime.utcnow(), strategy):
        logger.debug('Executing sell due to ROI ...')
        execute_sell(trade, current_rate)
        return True

    # Experimental: Check if the trade is profitable before selling it (avoid selling at loss)
    if _CONF.get('experimental', {}).get('sell_profit_only', False):
        logger.debug('Checking if trade is profitable ...')
        if not buy and trade.calc_profit(rate=current_rate) <= 0:
            return False

    # Experimental: Check if sell signal has been enabled and triggered
    if sell and not buy:
        logger.debug('Executing sell due to sell signal ...')
        execute_sell(trade, current_rate)
        return True

    return False


def get_target_bid(ticker: Dict[str, float]) -> float:
    """ Calculates bid target between current ask price and last price """
    if ticker['ask'] < ticker['last']:
        return ticker['ask']
    balance = _CONF['bid_strategy']['ask_last_balance']
    return ticker['ask'] + balance * (ticker['last'] - ticker['ask'])


def create_trade(stake_amount: float, strategy: str) -> bool:
    """
    Checks the implemented trading indicator(s) for a randomly picked pair,
    if one pair triggers the buy_signal a new trade record gets created
    :param stake_amount: amount of btc to spend
    :return: True if a trade object has been created and persisted, False otherwise
    """
    logger.debug(
        'Checking buy signals to create a new trade with stake_amount: %f ...',
        stake_amount
    )
    whitelist = copy.deepcopy(_CONF['exchange']['pair_whitelist'])
    # Check if stake_amount is fulfilled
    if exchange.get_balance(_CONF['stake_currency']) < stake_amount:
        raise DependencyException(
            'stake amount is not fulfilled (currency={})'.format(_CONF['stake_currency'])
        )

    # Remove currently opened and latest pairs from whitelist
    for trade in Trade.query.filter(Trade.is_open.is_(True)).all():
        if trade.pair in whitelist:
            whitelist.remove(trade.pair)
            logger.debug('Ignoring %s in pair whitelist', trade.pair)

    for _pair in _BLACKLIST:
        if _pair in whitelist:
            whitelist.remove(_pair)
            logger.debug('Ignoring %s in pair blacklist', trade.pair)

    if not whitelist:
        raise DependencyException('No pair in whitelist')

    # Pick pair based on StochRSI buy signals
    for _pair in whitelist:
        (buy, sell) = get_signal(_pair, strategy)
        if buy and not sell:
            pair = _pair
            break
    else:
        return False

    # Calculate amount
    buy_limit = get_target_bid(exchange.get_ticker(pair))
    amount = stake_amount / buy_limit

    try:
        order_id = exchange.buy(pair, buy_limit, amount)
    except TradeException as ex:
        rpc.send_msg('Blacklisting {} pair due to {}'.format(pair, ex))
        _BLACKLIST.add(pair)
        logger.warning('Add pair %s to blacklist', pair)
        return False

    fiat_converter = CryptoToFiatConverter()
    stake_amount_fiat = fiat_converter.convert_amount(
        stake_amount,
        _CONF['stake_currency'],
        _CONF['fiat_display_currency']
    )

    # Create trade entity and return
    rpc.send_msg('*{}:* Buying [{}]({}) with limit `{:.8f} ({:.6f} {}, {:.3f} {})` '.format(
        exchange.get_name().upper(),
        pair.replace('_', '/'),
        exchange.get_pair_detail_url(pair),
        buy_limit, stake_amount, _CONF['stake_currency'],
        stake_amount_fiat, _CONF['fiat_display_currency']
    ))
    # Fee is applied twice because we make a LIMIT_BUY and LIMIT_SELL
    trade = Trade(
        pair=pair,
        stake_amount=stake_amount,
        amount=amount,
        fee=exchange.get_fee(),
        open_rate=buy_limit,
        open_date=datetime.utcnow(),
        exchange=exchange.get_name().upper(),
        open_order_id=order_id
    )
    Trade.session.add(trade)
    Trade.session.flush()
    return True


def init(config: dict, db_url: Optional[str] = None) -> None:
    """
    Initializes all modules and updates the config
    :param config: config as dict
    :param db_url: database connector string for sqlalchemy (Optional)
    :return: None
    """
    # Initialize all modules
    rpc.init(config)
    persistence.init(config, db_url)
    exchange.init(config)

    # Set initial application state
    initial_state = config.get('initial_state')
    if initial_state:
        update_state(State[initial_state.upper()])
    else:
        update_state(State.STOPPED)


@cached(TTLCache(maxsize=1, ttl=1800))
def gen_pair_whitelist(base_currency: str, key: str = 'BaseVolume',
                       nb_assets: int = 0) -> List[str]:
    """
    Updates the whitelist with with a dynamically generated list
    :param base_currency: base currency as str
    :param key: sort key (defaults to 'BaseVolume')
    :return: List of pairs
    """
    summaries = sorted(
        (s for s in exchange.get_market_summaries() if s['MarketName'].startswith(base_currency)),
        key=lambda s: s.get(key) or 0.0,
        reverse=True
    )

    pairs = [s['MarketName'].replace('-', '_') for s in summaries]
    if nb_assets:
        pairs = pairs[:nb_assets]
    logger.info("Trading pairs: {}".format(pairs))
    return pairs


def cleanup() -> None:
    """
    Cleanup the application state und finish all pending tasks
    :return: None
    """
    rpc.send_msg('*Status:* `Stopping trader...`')
    logger.info('Stopping trader and cleaning up modules...')
    update_state(State.STOPPED)
    persistence.cleanup()
    rpc.cleanup()
    exit(0)


def init_args(sysargv) -> Watchdog:

    global _CONF

    args = parse_args(sysargv,
                      'Simple High Frequency Trading Bot for crypto currencies')

    # A subcommand has been issued
    if hasattr(args, 'func'):
        args.func(args)
        exit(0)

    # Initialize logger
    logging.basicConfig(
        level=args.loglevel,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )

    logger.info(
        'Starting freqtrade %s (loglevel=%s)',
        __version__,
        logging.getLevelName(args.loglevel)
    )

    # Load and validate configuration
    _CONF = load_config(args.config)

    # Add the strategy file to use
    _CONF.update({'strategy': args.strategy})

    # Initialize all modules and start main loop
    if args.dynamic_whitelist:
        logger.info('Using dynamically generated whitelist. (--dynamic-whitelist detected)')

    # If the user ask for Dry run with a local DB instead of memory
    if args.dry_run_db:
        if _CONF.get('dry_run', False):
            _CONF.update({'dry_run_db': True})
            logger.info(
                'Dry_run will use the DB file: "tradesv3.dry_run.sqlite". (--dry_run_db detected)'
            )
        else:
            logger.info('Dry run is disabled. (--dry_run_db ignored)')

    watchdog = Watchdog()

    if args.watchdog_enable:
        logger.info('Using watchdog to monitor process (--watchdog)')
        if not watchdog.start():
            exit(0)

    logger.info("Use strategy: {}".format(args.strategy))

    return args, watchdog


def main(sysargv=sys.argv[1:]) -> None:
    """
    Loads and validates the config and handles the main loop
    :return: None
    """
    global _CONF

    args, watchdog = init_args(sysargv)

    try:
        init(_CONF)
        old_state = None

        while True:
            new_state = get_state()
            # Log state transition
            if new_state != old_state:
                rpc.send_msg('*Status:* `{}`'.format(new_state.name.lower()))
                logger.info('Changing state to: %s', new_state.name)

            if new_state == State.STOPPED:
                time.sleep(1)
            elif new_state == State.RUNNING:
                throttle(
                    _process,
                    min_secs=_CONF['internals'].get('process_throttle_secs', 10),
                    nb_assets=args.dynamic_whitelist,
                    strategy=args.strategy
                )
            old_state = new_state
            watchdog.heartbeat()
    except KeyboardInterrupt:
        logger.info('Got SIGINT, aborting ...')
    except BaseException:
        logger.exception('Got fatal exception!')
    finally:
        cleanup()


if __name__ == '__main__':
    main()
