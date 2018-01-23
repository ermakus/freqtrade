from pandas import DataFrame
from user_data.strategies.base import BaseStrategy

# Update this variable if you change the class name
class_name = 'SmithStrategy'


class SmithStrategy(BaseStrategy):

    def populate_buy_trend(self, dataframe: DataFrame) -> DataFrame:
        dataframe.loc[
          (
              (dataframe['rsi'] < 50) &
              (dataframe['fastd'] < 50) &
              (dataframe['fastk'] < 50) &
              (dataframe['direction'].shift(3) < 0) &
              (dataframe['adx'].shift(3) > 20) &
              (dataframe['close'] > dataframe['open']) &
              (dataframe['close'].shift(1) > dataframe['open'].shift(1)) &
              (dataframe['close'].shift(2) > dataframe['open'].shift(2)) &
              (dataframe['close'] > dataframe['tema'])
          ),
          'buy'] = 1

        return dataframe
