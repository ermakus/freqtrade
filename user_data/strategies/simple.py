# Simple but surprisingly effective strategy
from pandas import DataFrame
from user_data.strategies.base import BaseStrategy

# Update this variable if you change the class name
class_name = 'SimpleStrategy'


class SimpleStrategy(BaseStrategy):

    def populate_buy_trend(self, dataframe: DataFrame) -> DataFrame:
        dataframe.loc[
            (
                (dataframe['fastd'] < 44) &
                (dataframe['rsi'] < 34) &
                (dataframe['ema50'] > dataframe['ema150'])
            ),
            'buy'] = 1
        return dataframe
