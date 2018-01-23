"""
Functions to analyze ticker data with indicators and produce buy and sell signals
"""
import logging
from datetime import timedelta
from enum import Enum
from typing import Dict, List
import arrow
from pandas import DataFrame, to_datetime

from freqtrade.exchange import get_ticker_history
from freqtrade.strategy.strategy import Strategy

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """ Enum to distinguish between buy and sell signals """
    BUY = "buy"
    SELL = "sell"


def parse_ticker_dataframe(ticker: list) -> DataFrame:
    """
    Analyses the trend for the given ticker history
    :param ticker: See exchange.get_ticker_history
    :return: DataFrame
    """
    columns = {'C': 'close', 'V': 'volume', 'O': 'open', 'H': 'high', 'L': 'low', 'T': 'date'}
    frame = DataFrame(ticker) \
        .rename(columns=columns)
    if 'BV' in frame:
        frame.drop('BV', 1, inplace=True)
    frame['date'] = to_datetime(frame['date'], utc=True, infer_datetime_format=True)
    frame.sort_values('date', inplace=True)
    return frame


def analyze_ticker(ticker_history: List[Dict], strategy: Strategy) -> DataFrame:
    """
    Parses the given ticker history and returns a populated DataFrame
    add several TA indicators and buy signal to it
    :return DataFrame with ticker data and indicator data
    """
    dataframe = parse_ticker_dataframe(ticker_history)
    dataframe = strategy.populate_indicators(dataframe)
    dataframe = strategy.populate_buy_trend(dataframe)
    dataframe = strategy.populate_sell_trend(dataframe)
    return dataframe


def get_signal(pair: str, strategy: Strategy) -> (bool, bool):
    """
    Calculates current signal based several technical analysis indicators
    :param pair: pair in format BTC_ANT or BTC-ANT
    :return: (True, False) if pair is good for buying and not for selling
    """
    ticker_hist = get_ticker_history(pair, strategy.ticker_interval)
    if not ticker_hist:
        logger.warning('Empty ticker history for pair %s', pair)
        return (False, False)

    try:
        dataframe = analyze_ticker(ticker_hist, strategy)
    except ValueError as ex:
        logger.warning('Unable to analyze ticker for pair %s: %s', pair, str(ex))
        return (False, False)
    except Exception as ex:
        logger.exception('Unexpected error when analyzing ticker for pair %s: %s', pair, str(ex))
        return (False, False)

    if dataframe.empty:
        return (False, False)

    latest = dataframe.iloc[-1]

    # Check if dataframe is out of date
    signal_date = arrow.get(latest['date'])
    if signal_date < arrow.now() - timedelta(minutes=10):
        return (False, False)

    (buy, sell) = latest[SignalType.BUY.value] == 1, latest[SignalType.SELL.value] == 1
    logger.debug('trigger: %s (pair=%s) buy=%s sell=%s', latest['date'], pair, str(buy), str(sell))
    return (buy, sell)
