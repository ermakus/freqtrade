#!/usr/bin/env python3
import sys
import logging
import argparse

import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from pandas import DataFrame
import talib.abstract as ta

import freqtrade.vendor.qtpylib.indicators as qtpylib
from freqtrade import exchange, analyze
from freqtrade.misc import common_args_parser
from freqtrade.strategy.strategy import Strategy
import freqtrade.misc as misc
import freqtrade.optimize as optimize
import freqtrade.analyze as analyze


logger = logging.getLogger(__name__)


def plot_parse_args(args):
    parser = misc.common_args_parser('Graph dataframe')
    misc.backtesting_options(parser)
    misc.scripts_options(parser)
    return parser.parse_args(args)


def plot_analyzed_dataframe(args) -> None:
    """
    Calls analyze() and plots the returned dataframe
    :param pair: pair as str
    :return: None
    """
    pair = args.pair
    pairs = [pair]
    timerange = misc.parse_timerange(args.timerange)

    # Init strategy
    strategy = Strategy({'strategy': args.strategy})
    tick_interval = strategy.ticker_interval
    exchange._API = exchange.Bittrex({'key': '', 'secret': ''})

    tickers = {}
    if args.live:
        logger.info('Downloading pair.')
        # Init Bittrex to use public API
        tickers[pair] = exchange.get_ticker_history(pair, tick_interval)
    else:
        tickers = optimize.load_data(args.datadir, pairs=pairs,
                                     ticker_interval=tick_interval,
                                     refresh_pairs=False,
                                     timerange=timerange)
    dataframes = optimize.tickerdata_to_dataframe(tickers, strategy)
    dataframe = dataframes[pair]
    dataframe = strategy.populate_buy_trend(dataframe)
    dataframe = strategy.populate_sell_trend(dataframe)
    dates = misc.datesarray_to_datetimearray(dataframe['date'])

    # Two subplots sharing x axis
    fig, (ax1, ax2, ax3) = plt.subplots(3, sharex=True)
    fig.suptitle(pair + " " +     str(tick_interval), fontsize=14, fontweight='bold')

    ax1.plot(dates, dataframe['close'], label='close')
    # ax1.plot(dates, dataframe['sell'], 'ro', label='sell')
    ax1.plot(dates, dataframe['sma'], '--', label='SMA')
    ax1.plot(dates, dataframe['tema'], ':', label='TEMA')
    ax1.plot(dates, dataframe['blower'], '-.', label='BB low')
    ax1.plot(dates, dataframe['close'] * dataframe['buy'], 'bo', label='buy')
    ax1.plot(dates, dataframe['close'] * dataframe['sell'], 'ro', label='sell')

    ax1.legend()

    ax2.plot(dates, dataframe['adx'], label='ADX')
    ax2.plot(dates, dataframe['mfi'], label='MFI')
    # ax2.plot(dates, [25] * len(dataframe.index.values))
    ax2.legend()

    ax3.plot(dates, dataframe['fastk'], label='k')
    ax3.plot(dates, dataframe['fastd'], label='d')
    ax3.plot(dates, [20] * len(dataframe.index.values))
    ax3.legend()
    xfmt = mdates.DateFormatter('%d-%m-%y %H:%M')  # Dont let matplotlib autoformat date
    ax3.xaxis.set_major_formatter(xfmt)

    # Fine-tune figure; make subplots close to each other and hide x ticks for
    # all but bottom plot.
    fig.subplots_adjust(hspace=0)
    fig.autofmt_xdate()  # Rotate the dates
    plt.setp([a.get_xticklabels() for a in fig.axes[:-1]], visible=False)
    plt.show()

if __name__ == '__main__':
    args = plot_parse_args(sys.argv[1:])
    plot_analyzed_dataframe(args)
