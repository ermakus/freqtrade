"""
Default strategy
"""
from pandas import DataFrame
import talib.abstract as ta


def populate_indicators(dataframe: DataFrame) -> DataFrame:
    dataframe['rsi'] = ta.RSI(dataframe)
    stoch_fast = ta.STOCHF(dataframe)
    dataframe['fastd'] = stoch_fast['fastd']
    dataframe['fastk'] = stoch_fast['fastk']
    dataframe['ema50'] = ta.EMA(dataframe, timeperiod=50)
    dataframe['ema150'] = ta.EMA(dataframe, timeperiod=150)
    dataframe['cci'] = ta.CCI(dataframe, timeperiod=200)
    return dataframe


def populate_buy_trend(dataframe: DataFrame) -> DataFrame:
    dataframe.loc[
        (
            (dataframe['fastd'] < 44) &
            (dataframe['rsi'] < 34) &
            (dataframe['ema50'] > dataframe['ema150'])
        ),
        'buy'] = 1
    return dataframe


def populate_sell_trend(dataframe: DataFrame) -> DataFrame:
    dataframe['sell'] = 0
    return dataframe
