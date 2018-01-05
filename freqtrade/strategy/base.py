"""
Base (original) strategy, used in unitetests
"""
from pandas import DataFrame
from freqtrade.vendor.qtpylib.indicators import crossed_above


def populate_buy_trend(dataframe: DataFrame) -> DataFrame:
    dataframe.loc[
        (
            (dataframe['rsi'] < 35) &
            (dataframe['fastd'] < 35) &
            (dataframe['adx'] > 30) &
            (dataframe['plus_di'] > 0.5)
        ) |
        (
            (dataframe['adx'] > 65) &
            (dataframe['plus_di'] > 0.5)
        ),
        'buy'] = 1

    return dataframe


def populate_sell_trend(dataframe: DataFrame) -> DataFrame:
    dataframe.loc[
        (
            (
                (crossed_above(dataframe['rsi'], 70)) |
                (crossed_above(dataframe['fastd'], 70))
            ) &
            (dataframe['adx'] > 10) &
            (dataframe['minus_di'] > 0)
        ) |
        (
            (dataframe['adx'] > 70) &
            (dataframe['minus_di'] > 0.5)
        ),
        'sell'] = 1
    return dataframe
