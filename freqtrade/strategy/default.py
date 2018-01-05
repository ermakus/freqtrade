"""
Default strategy
"""
from pandas import DataFrame


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
