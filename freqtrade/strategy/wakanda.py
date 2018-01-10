"""
Strategy by @Wakanda
"""
from pandas import DataFrame
import talib.abstract as ta


def populate_indicators(dataframe: DataFrame) -> DataFrame:
    dataframe['ema5'] = ta.EMA(dataframe, timeperiod=5)
    dataframe['mean-volume'] = dataframe['volume'].mean() * 10
    dataframe['cci'] = ta.CCI(dataframe, 5)
    stoch = ta.STOCHF(dataframe, 5)
    dataframe['fastd'] = stoch['fastd']
    dataframe['fastk'] = stoch['fastk']
    dataframe['adx'] = ta.ADX(dataframe, 5)
    dataframe['slowadx'] = ta.ADX(dataframe, 35)
    slowstoch = ta.STOCHF(dataframe, 50)
    dataframe['slowfastd'] = slowstoch['fastd']
    dataframe['slowfastk'] = slowstoch['fastk']
    dataframe['fastk-previous'] = dataframe.fastk.shift(1)
    dataframe['fastd-previous'] = dataframe.fastd.shift(1)
    dataframe['slowfastk-previous'] = dataframe.slowfastk.shift(1)
    dataframe['slowfastd-previous'] = dataframe.slowfastd.shift(1)
    return dataframe

def populate_buy_trend(dataframe: DataFrame) -> DataFrame:
    dataframe.loc[
        ((dataframe['adx'] > 50) | (dataframe['slowadx'] > 26)) & 
        (dataframe['cci'] < -100) &
        (dataframe['fastk-previous'] < 20) & (dataframe['fastd-previous'] < 20) &
        (dataframe['slowfastk-previous'] < 30) & (dataframe['slowfastd-previous'] < 30) &
        (dataframe['fastk-previous'] < dataframe['fastd-previous']) & (dataframe['fastk'] > dataframe['fastd']) &
        (dataframe['mean-volume'] > 0.75) & (dataframe['close'] > 0.00000100),
        'buy'] = 1
    return dataframe


def populate_sell_trend(dataframe: DataFrame) -> DataFrame:
    dataframe.loc[ 
        (dataframe['slowadx'] < 25) & 
        ((dataframe['fastk'] > 70) | (dataframe['fastd'] > 70)) &
        (dataframe['fastk-previous'] < dataframe['fastd-previous']) &
        (dataframe['close'] > dataframe['ema5']),
        'sell'] = 1
    return dataframe
