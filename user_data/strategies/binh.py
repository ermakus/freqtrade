"""
Strategy by @Wakanda
"""
from pandas import DataFrame
import talib.abstract as ta
from user_data.strategies.base import BaseStrategy

# Update this variable if you change the class name
class_name = 'BinhStrategy'


class BinhStrategy(BaseStrategy):

    def populate_indicators(self, dataframe: DataFrame) -> DataFrame:
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=5)
        rsiframe = DataFrame(dataframe['rsi']).rename(columns={'rsi': 'close'})
        dataframe['emarsi'] = ta.EMA(rsiframe, timeperiod=5)
        macd = ta.MACD(dataframe)
        dataframe['macd'] = macd['macd']
        dataframe['adx'] = ta.ADX(dataframe)

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame) -> DataFrame:
        dataframe.loc[
            (
              dataframe['adx'].gt(20) &
              dataframe['emarsi'].le(40) &
              dataframe['macd'].lt(0)
            ),
            'buy'] = 1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame) -> DataFrame:
        dataframe.loc[
            (
              dataframe['adx'].gt(20) &
              dataframe['macd'].gt(0) &
              dataframe['emarsi'].ge(70)
            ),
            'sell'] = 1
        return dataframe
