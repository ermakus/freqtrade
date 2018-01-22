"""
Default strategy
"""
from pandas import DataFrame
import talib.abstract as ta

def populate_buy_trend(dataframe: DataFrame) -> DataFrame:
    dataframe.loc[
        (
            (dataframe['rsi'] < 35) &
            (dataframe['fastd'] < 25) &
            (dataframe['fastk'] < 25) &
            ((dataframe['adx'] < 15) | (dataframe['adx'] > 45)) &
            (dataframe['plus_di'] < 10) &
            (dataframe['minus_di'] > 25)
        ),
        'buy'] = 1

    return dataframe


def populate_sell_trend(dataframe: DataFrame) -> DataFrame:
    dataframe.loc[
        (
            (dataframe['rsi'] > 55) &
            (dataframe['fastd'] > 45) &
            (dataframe['fastk'] > 45) &
            ((dataframe['adx'] > 25) | (dataframe['adx'] < 25)) &
            (dataframe['plus_di'] > 45) &
            (dataframe['minus_di'] < 25)
        ),
        'sell'] = 1
    return dataframe
