"""
Strategy by @baudbox
"""
from pandas import DataFrame


def populate_buy_trend(dataframe: DataFrame) -> DataFrame:
    dataframe.loc[
        (dataframe['close'] > 0.00001000) &
        (dataframe['cci'] < -90.0) &
        (dataframe['fastd'] < 15) & (dataframe['fastk'] < 15) &
        (dataframe['fastk'] < dataframe['fastd']) &
        (dataframe['adx'] > 15),
        'buy'] = 1
    return dataframe


def populate_sell_trend(dataframe: DataFrame) -> DataFrame:
    dataframe['sell'] = 0
    return dataframe
