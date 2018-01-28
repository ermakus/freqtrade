import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame


class_name = 'BTFDSTFHStrategy'


class BTFDSTFHStrategy(IStrategy):
    """
    Buy the Fine Dip/Sell The Fine High Strategy
    https://www.youtube.com/watch?v=0akBdQa55b4
    Michael Smith rybolov@rybolov.net
    """

    # Minimal ROI designed for the strategy
    minimal_roi = {
        "60":  0.0,
        "50":  0.01,
        "40":  0.02,
        "30":  0.03,
        "0":  0.09
    }

    # Optimal stoploss designed for the strategy
    stoploss = -0.20

    # Optimal ticker interval for the strategy
    ticker_interval = 5

    def populate_indicators(self, dataframe: DataFrame) -> DataFrame:
        """
        Adds several different TA indicators to the given DataFrame

        Performance Note: For the best performance be frugal on the number of indicators
        you are using. Let uncomment only the indicator you are using in your strategies
        or your hyperopt configuration, otherwise you will waste your memory and CPU usage.
        """

        # Momentum Indicator
        # ------------------------------------

        # ADX
        dataframe['adx'] = ta.ADX(dataframe)

        # Awesome oscillator
        dataframe['ao'] = qtpylib.awesome_oscillator(dataframe)

        # Commodity Channel Index: values Oversold:<-100, Overbought:>100
        dataframe['cci'] = ta.CCI(dataframe)

        # MACD
        macd = ta.MACD(dataframe)
        dataframe['macd'] = macd['macd']
        dataframe['macdsignal'] = macd['macdsignal']
        dataframe['macdhist'] = macd['macdhist']

        # MFI
        dataframe['mfi'] = ta.MFI(dataframe)

        # Minus Directional Indicator / Movement
        dataframe['minus_dm'] = ta.MINUS_DM(dataframe)
        dataframe['minus_di'] = ta.MINUS_DI(dataframe)
        dataframe['fastminus_dm'] = ta.MINUS_DM(dataframe, timeperiod=1)
        dataframe['longminus_dm'] = ta.MINUS_DM(dataframe, timeperiod=60)
        dataframe['longlongminus_dm'] = ta.MINUS_DM(dataframe, timeperiod=200)

        # Plus Directional Indicator / Movement
        dataframe['plus_dm'] = ta.PLUS_DM(dataframe)
        dataframe['plus_di'] = ta.PLUS_DI(dataframe)
        dataframe['fastplus_dm'] = ta.PLUS_DM(dataframe, timeperiod=1)
        dataframe['longplus_dm'] = ta.PLUS_DM(dataframe, timeperiod=60)
        dataframe['longlongplus_dm'] = ta.PLUS_DM(dataframe, timeperiod=200)

        dataframe['direction'] = dataframe['plus_dm'] - dataframe['minus_dm']
        dataframe['fastdirection'] = dataframe['fastplus_dm'] - dataframe['fastminus_dm']
        dataframe['longdirection'] = dataframe['longplus_dm'] - dataframe['longminus_dm']
        dataframe['longlongdirection'] = dataframe['longlongplus_dm'] - dataframe['longlongminus_dm']  # noqa

        """
        # ROC
        dataframe['roc'] = ta.ROC(dataframe)
        """
        # RSI
        dataframe['rsi'] = ta.RSI(dataframe)
        """
        # Inverse Fisher transform on RSI, values [-1.0, 1.0] (https://goo.gl/2JGGoy)
        rsi = 0.1 * (dataframe['rsi'] - 50)
        dataframe['fisher_rsi'] = (numpy.exp(2 * rsi) - 1) / (numpy.exp(2 * rsi) + 1)
        # Inverse Fisher transform on RSI normalized, value [0.0, 100.0] (https://goo.gl/2JGGoy)
        dataframe['fisher_rsi_norma'] = 50 * (dataframe['fisher_rsi'] + 1)
        # Stoch
        stoch = ta.STOCH(dataframe)
        dataframe['slowd'] = stoch['slowd']
        dataframe['slowk'] = stoch['slowk']
        """
        # Stoch fast
        stoch_fast = ta.STOCHF(dataframe)
        dataframe['fastd'] = stoch_fast['fastd']
        dataframe['fastk'] = stoch_fast['fastk']
        """
        # Stoch RSI
        stoch_rsi = ta.STOCHRSI(dataframe)
        dataframe['fastd_rsi'] = stoch_rsi['fastd']
        dataframe['fastk_rsi'] = stoch_rsi['fastk']
        """

        dataframe['longrsi'] = ta.RSI(dataframe, timeperiod=200)
        dataframe['longmfi'] = ta.MFI(dataframe, timeperiod=200)

        # Overlap Studies
        # ------------------------------------

        # Previous Bollinger bands
        # Because ta.BBANDS implementation is broken with small numbers, it actually
        # returns middle band for all the three bands. Switch to qtpylib.bollinger_bands
        # and use middle band instead.
        dataframe['blower'] = ta.BBANDS(dataframe, nbdevup=2, nbdevdn=2)['lowerband']

        # Bollinger bands
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_lowerband'] = bollinger['lower']
        dataframe['bb_middleband'] = bollinger['mid']
        dataframe['bb_upperband'] = bollinger['upper']

        # EMA - Exponential Moving Average
        dataframe['ema3'] = ta.EMA(dataframe, timeperiod=3)
        dataframe['ema5'] = ta.EMA(dataframe, timeperiod=5)
        dataframe['ema10'] = ta.EMA(dataframe, timeperiod=10)
        dataframe['ema50'] = ta.EMA(dataframe, timeperiod=50)
        dataframe['ema100'] = ta.EMA(dataframe, timeperiod=100)

        # SAR Parabol
        dataframe['sar'] = ta.SAR(dataframe)

        # SMA - Simple Moving Average
        dataframe['sma'] = ta.SMA(dataframe, timeperiod=40)

        # TEMA - Triple Exponential Moving Average
        dataframe['tema'] = ta.TEMA(dataframe, timeperiod=9)

        # Cycle Indicator
        # ------------------------------------
        # Hilbert Transform Indicator - SineWave
        hilbert = ta.HT_SINE(dataframe)
        dataframe['htsine'] = hilbert['sine']
        dataframe['htleadsine'] = hilbert['leadsine']

        # Pattern Recognition - Bullish candlestick patterns
        # ------------------------------------
        """
        # Hammer: values [0, 100]
        dataframe['CDLHAMMER'] = ta.CDLHAMMER(dataframe)
        # Inverted Hammer: values [0, 100]
        dataframe['CDLINVERTEDHAMMER'] = ta.CDLINVERTEDHAMMER(dataframe)
        # Dragonfly Doji: values [0, 100]
        dataframe['CDLDRAGONFLYDOJI'] = ta.CDLDRAGONFLYDOJI(dataframe)
        # Piercing Line: values [0, 100]
        dataframe['CDLPIERCING'] = ta.CDLPIERCING(dataframe) # values [0, 100]
        # Morningstar: values [0, 100]
        dataframe['CDLMORNINGSTAR'] = ta.CDLMORNINGSTAR(dataframe) # values [0, 100]
        # Three White Soldiers: values [0, 100]
        dataframe['CDL3WHITESOLDIERS'] = ta.CDL3WHITESOLDIERS(dataframe) # values [0, 100]
        """

        # Pattern Recognition - Bearish candlestick patterns
        # ------------------------------------
        """
        # Hanging Man: values [0, 100]
        dataframe['CDLHANGINGMAN'] = ta.CDLHANGINGMAN(dataframe)
        # Shooting Star: values [0, 100]
        dataframe['CDLSHOOTINGSTAR'] = ta.CDLSHOOTINGSTAR(dataframe)
        # Gravestone Doji: values [0, 100]
        dataframe['CDLGRAVESTONEDOJI'] = ta.CDLGRAVESTONEDOJI(dataframe)
        # Dark Cloud Cover: values [0, 100]
        dataframe['CDLDARKCLOUDCOVER'] = ta.CDLDARKCLOUDCOVER(dataframe)
        # Evening Doji Star: values [0, 100]
        dataframe['CDLEVENINGDOJISTAR'] = ta.CDLEVENINGDOJISTAR(dataframe)
        # Evening Star: values [0, 100]
        dataframe['CDLEVENINGSTAR'] = ta.CDLEVENINGSTAR(dataframe)
        """

        # Pattern Recognition - Bullish/Bearish candlestick patterns
        # ------------------------------------
        """
        # Three Line Strike: values [0, -100, 100]
        dataframe['CDL3LINESTRIKE'] = ta.CDL3LINESTRIKE(dataframe)
        # Spinning Top: values [0, -100, 100]
        dataframe['CDLSPINNINGTOP'] = ta.CDLSPINNINGTOP(dataframe) # values [0, -100, 100]
        # Engulfing: values [0, -100, 100]
        dataframe['CDLENGULFING'] = ta.CDLENGULFING(dataframe) # values [0, -100, 100]
        # Harami: values [0, -100, 100]
        dataframe['CDLHARAMI'] = ta.CDLHARAMI(dataframe) # values [0, -100, 100]
        # Three Outside Up/Down: values [0, -100, 100]
        dataframe['CDL3OUTSIDE'] = ta.CDL3OUTSIDE(dataframe) # values [0, -100, 100]
        # Three Inside Up/Down: values [0, -100, 100]
        dataframe['CDL3INSIDE'] = ta.CDL3INSIDE(dataframe) # values [0, -100, 100]
        """

        # Chart type
        # ------------------------------------
        # Heikinashi stategy
        heikinashi = qtpylib.heikinashi(dataframe)
        dataframe['ha_open'] = heikinashi['open']
        dataframe['ha_close'] = heikinashi['close']
        dataframe['ha_high'] = heikinashi['high']
        dataframe['ha_low'] = heikinashi['low']

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame) -> DataFrame:
        """
        Based on TA indicators, populates the buy signal for the given dataframe
        :param dataframe: DataFrame
        :return: DataFrame with buy column
        """
        # Very Good, use this.
        dataframe.loc[
            (
                (dataframe['rsi'] < 47) &
                (dataframe['rsi'] > 0) &
                (dataframe['fastd'] < 47) &
                (dataframe['fastd'] > 0) &
                (dataframe['close'] > dataframe['open']) &
                (dataframe['close'].shift(1) > dataframe['open'].shift(1)) &
                (dataframe['close'].shift(2) > dataframe['open'].shift(2)) &
                (dataframe['cci'] < -70) &
                (dataframe['cci'] > -500000000)
            ),
            'buy'] = 1

        # Good, use this.
        dataframe.loc[
            (
                (dataframe['rsi'] < 37) &
                (dataframe['rsi'] > 0) &
                (dataframe['fastd'] < 37) &
                (dataframe['fastd'] > 0) &
                (dataframe['close'] > dataframe['tema']) &
                (dataframe['close'] > dataframe['open']) &
                (dataframe['close'].shift(1) > dataframe['open'].shift(1)) &
                (dataframe['close'].shift(2) > dataframe['open'].shift(2)) &
                (dataframe['cci'] < -70) &
                (dataframe['cci'] > -500000000)
            ),
            'buy'] = 1

        # Good, use this.
        dataframe.loc[
            (
                (dataframe['rsi'] < 37) &
                (dataframe['rsi'] > 0) &
                (dataframe['fastk'] < 40) &
                (dataframe['fastk'] > 0) &
                (dataframe['close'] > dataframe['tema']) &
                (dataframe['close'] > dataframe['open']) &
                (dataframe['close'].shift(1) > dataframe['open'].shift(1)) &
                (dataframe['close'].shift(2) > dataframe['open'].shift(2)) &
                (dataframe['cci'] < -70) &
                (dataframe['cci'] > -500000000)
            ),
            'buy'] = 1

        # Works Great
        dataframe.loc[
            (
                (dataframe['cci'] < -70) &
                (dataframe['cci'] > -500000000) &
                (dataframe['mfi'] < 30) &
                (dataframe['mfi'] > 0) &
                (dataframe['close'] > dataframe['open']) &
                (dataframe['close'].shift(1) > dataframe['open'].shift(1)) &
                (dataframe['close'].shift(2) > dataframe['open'].shift(2)) &
                (dataframe['tema'] > 0) &
                (dataframe['close'] > dataframe['tema'])
            ),
            'buy'] = 1

        # Good, use this.
        dataframe.loc[
            (
                (dataframe['cci'] < 0) &
                (dataframe['cci'] > -500000000) &
                (dataframe['mfi'] < 42) &
                (dataframe['mfi'] > 0) &
                (dataframe['rsi'] < 45) &
                (dataframe['rsi'] > 0) &
                (dataframe['fastd'] < 45) &
                (dataframe['fastd'] > 0) &
                (dataframe['close'] > dataframe['open']) &
                (dataframe['close'].shift(1) > dataframe['open'].shift(1)) &
                (dataframe['close'].shift(2) > dataframe['open'].shift(2)) &
                (dataframe['tema'] > 0) &
                (dataframe['close'] > dataframe['tema'])
            ),
            'buy'] = 1

        # Good, use this.
        dataframe.loc[
            (
                (dataframe['adx'].shift(3) > 30) &
                (dataframe['direction'].shift(3) < 0) &
                (dataframe['mfi'] < 30) &
                (dataframe['close'] > dataframe['open']) &
                (dataframe['close'].shift(1) > dataframe['open'].shift(1)) &
                (dataframe['close'].shift(2) > dataframe['open'].shift(2)) &
                (dataframe['tema'] > 0) &
                (dataframe['close'] > dataframe['tema']) &
                (dataframe['longdirection'].shift(3) < 0) &
                (dataframe['longlongdirection'].shift(3) < 0)
            ),
            'buy'] = 1

        """
        #Works, needs help
        dataframe.loc[
            (
                (dataframe['mfi'] < 25) &
                (dataframe['tema'] > 0) &
                (dataframe['close'] > dataframe['tema'])
            ),
            'buy'] = 1

        """
        # Testing, works really well.
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
        """
        #Testing, needs a lot of work.
        dataframe.loc[
            (
                (dataframe['cci'] < 60) &
                (dataframe['cci'] > -500000000) &
                (dataframe['mfi'] < 60) &
                (dataframe['rsi'] < 60) &
                (dataframe['adx'] > 90) &
                (dataframe['direction'] > 0) &
                (dataframe['longdirection'] > 0) &
                (dataframe['longlongdirection'] > 0) &
                (dataframe['tema'] > 0) &
                (dataframe['close'] > dataframe['tema'])
            ),
            'buy'] = 1
        """

        """
        #Testing, needs a lot of work.
        dataframe.loc[
            (
                (dataframe['cci'] < 60) &
                (dataframe['cci'] > -500000000) &
                (dataframe['mfi'] < 60) &
                (dataframe['mfi'] > 0) &
                (dataframe['rsi'] < 60) &
                (dataframe['rsi'] > 0) &
                (dataframe['adx'] > 60) &
                (dataframe['tema'] <= dataframe['blower']) &
                (dataframe['tema'] > dataframe['tema'].shift(1)) &
                (dataframe['close'] > dataframe['tema'])
            ),
            'buy'] = 1
        """
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame) -> DataFrame:
        """
        Based on TA indicators, populates the sell signal for the given dataframe
        :param dataframe: DataFrame
        :return: DataFrame with buy column
        """
        dataframe.loc[
           (
               (
                   (qtpylib.crossed_above(dataframe['rsi'], 85)) |
                   (qtpylib.crossed_above(dataframe['fastd'], 85)) |
                   (qtpylib.crossed_above(dataframe['fastk'], 85)) |
                   (qtpylib.crossed_above(dataframe['cci'], 90)) |
                   (qtpylib.crossed_above(dataframe['mfi'], 85))
               ) &
               (dataframe['close'] < dataframe['open']) &
               (dataframe['close'].shift(1) < dataframe['open'].shift(1)) &
               (dataframe['close'].shift(2) < dataframe['open'].shift(2)) &
               (dataframe['close'].shift(3) < dataframe['open'].shift(3))
           ),
           'sell'] = 1

        return dataframe