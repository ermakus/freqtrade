from hyperopt import hp
from pandas import DataFrame
from functools import reduce
from freqtrade.vendor.qtpylib.indicators import crossed_above

SPACE = {
    'rsi': hp.choice('rsi', [
        {'enabled': False},
        {'enabled': True, 'value': hp.quniform('rsi-value', 20, 40, 1)}
    ]),
    'rsi_supp0': hp.choice('rsi_supp0', [
        {'enabled': False},
        {'enabled': True}
    ]),
    'close_sma': hp.choice('close_sma', [
        {'enabled': False},
        {'enabled': True}
    ]),
    'fisher_rsi': hp.choice('fisher_rsi', [
        {'enabled': False},
        {'enabled': True, 'value': hp.quniform('fisher_rsi-value', -0.96, 0.99, 1)}
    ]),
    'fisher_rsi_norma': hp.choice('fisher_rsi_norma', [
        {'enabled': False},
        {'enabled': True, 'value': hp.quniform('fisher_rsi_norma-value', 0.0, 100, 0.1)}
    ]),
    'mfi': hp.choice('mfi', [
        {'enabled': False},
        {'enabled': True, 'value': hp.quniform('mfi-value', 5, 25, 0.1)}
    ]),
    'uptrend_long_ema': hp.choice('uptrend_long_ema', [
        {'enabled': False},
        {'enabled': True}
    ]),
    'fastd_fastk': hp.choice('fastd_fastk', [
        {'enabled': False},
        {'enabled': True}
    ]),
    'fastd_fastk_rsi': hp.choice('fastd_fastk_rsi', [
        {'enabled': False},
        {'enabled': True}
    ]),
    'fastd_supp0': hp.choice('fastd_supp0', [
        {'enabled': False},
        {'enabled': True}
    ]),
    'volume': hp.choice('volume', [
        {'enabled': False},
        {'enabled': True, 'value': hp.quniform('volume-value', 1, 10, 1)}
    ]),
    'close': hp.choice('close', [
        {'enabled': False},
        {'enabled': True, 'value': hp.quniform('close-value', 0.00000100, 0.00000800, 1)}
    ]),
    'fastd': hp.choice('fastd', [
        {'enabled': False},
        {'enabled': True, 'value': hp.quniform('fastd-value', 10, 50, 1)}
    ]),
    'adx': hp.choice('adx', [
        {'enabled': False},
        {'enabled': True, 'value': hp.quniform('adx-value', 15, 50, 1)}
    ]),
    'cci': hp.choice('cci', [
        {'enabled': False},
        {'enabled': True, 'value': hp.quniform('cci-value', -100.0, 100.0, 0.1)}
    ]),
    'uptrend_short_ema': hp.choice('uptrend_short_ema', [
        {'enabled': False},
        {'enabled': True}
    ]),
    'over_sar': hp.choice('over_sar', [
        {'enabled': False},
        {'enabled': True}
    ]),
    'green_candle': hp.choice('green_candle', [
        {'enabled': False},
        {'enabled': True}
    ]),
    'uptrend_sma': hp.choice('uptrend_sma', [
        {'enabled': False},
        {'enabled': True}
    ]),
    'heikinashi': hp.choice('heikinashi', [
        {'enabled': False},
        {'enabled': True}
    ]),
    'CDLDRAGONFLYDOJI': hp.choice('CDLDRAGONFLYDOJI', [
        {'enabled': False},
        {'enabled': True}
    ]),
    'trigger': hp.choice('trigger', [
        {'type': 'lower_bb'},
        {'type': 'faststoch10'},
        {'type': 'ao_cross_zero'},
        {'type': 'ema50_cross_ema100'},
        {'type': 'ema5_cross_ema10'},
        {'type': 'macd_cross_signal'},
        {'type': 'sar_reversal'},
        {'type': 'stochf_cross'},
        {'type': 'ht_sine'},
        {'type': 'cci_cross_100'},
    ]),
}


def buy_strategy_generator(params):  # noqa C901
    def populate_buy_trend(dataframe: DataFrame) -> DataFrame:
        conditions = []
        # GUARDS AND TRENDS

        # Simulation for Option 2
        if 'adx' in params and params['adx']['enabled']:
            conditions.append(dataframe['adx'] > params['adx']['value'])

        if 'close' in params and params['close']['enabled']:
            conditions.append(dataframe['close'] > params['close']['value'])

        if 'volume' in params and params['volume']['enabled']:
            conditions.append(
                dataframe['volume'] > dataframe['volume'].mean() * params['volume']['value']
            )

        if 'close_sma' in params and params['close_sma']['enabled']:
            conditions.append(dataframe['close'] < dataframe['sma'])

        if 'fastd' in params and params['fastd']['enabled']:
            conditions.append(dataframe['fastd'] < params['fastd']['value'])

        if 'fastd_fastk' in params and params['fastd_fastk']['enabled']:
            conditions.append(dataframe['fastd'] > dataframe['fastk'])

        if 'fastd_fastk_rsi' in params and params['fastd_fastk_rsi']['enabled']:
            conditions.append(dataframe['fastd_rsi'] > dataframe['fastk_rsi'])

        if 'fastd_supp0' in params and params['fastd_supp0']['enabled']:
            conditions.append(dataframe['fastd'] > 0)

        if 'rsi_supp0' in params and params['rsi_supp0']['enabled']:
            conditions.append(dataframe['rsi'] > 0)

        if 'fisher_rsi' in params and params['fisher_rsi']['enabled']:
            conditions.append(dataframe['fisher_rsi'] < params['fisher_rsi']['value'])

        if 'fisher_rsi_norma' in params and params['fisher_rsi_norma']['enabled']:
            conditions.append(dataframe['fisher_rsi_norma'] < params['fisher_rsi_norma']['value'])

        if 'rsi' in params and params['rsi']['enabled']:
            conditions.append(dataframe['rsi'] < params['rsi']['value'])

        if 'mfi' in params and params['mfi']['enabled']:
            conditions.append(dataframe['mfi'] < params['mfi']['value'])

        if 'uptrend_sma' in params and params['uptrend_sma']['enabled']:
            prevsma = dataframe['sma'].shift(1)
            conditions.append(dataframe['sma'] > prevsma)

        if 'uptrend_long_ema' in params and params['uptrend_long_ema']['enabled']:
            conditions.append(dataframe['ema50'] > dataframe['ema100'])

        if 'uptrend_short_ema' in params and params['uptrend_short_ema']['enabled']:
            conditions.append(dataframe['ema5'] > dataframe['ema10'])

        if 'green_candle' in params and params['green_candle']['enabled']:
            conditions.append(dataframe['close'] > dataframe['open'])

        if 'over_sar' in params and params['over_sar']['enabled']:
            conditions.append(dataframe['close'] > dataframe['sar'])

        if 'cci' in params and params['cci']['enabled']:
            conditions.append(dataframe['cci'] > params['cci']['value'])

        if 'heikinashi' in params and params['heikinashi']['enabled']:
            conditions.append(
                (dataframe['ha_open'] < dataframe['ha_close']) &  # green bar
                (dataframe['ha_open'].shift(1) < dataframe['ha_close'].shift(1)) &  # green bar
                (dataframe['ha_low'].shift(1) > dataframe['ha_low'].shift(2)) &  # higher low

                (dataframe['ha_open'].shift(2) > dataframe['ha_close'].shift(2)) &  # red bar
                (dataframe['ha_open'].shift(3) > dataframe['ha_close'].shift(3)) &  # red bar
                (dataframe['ha_open'].shift(4) > dataframe['ha_close'].shift(4)) &  # red bar
                (dataframe['ha_open'].shift(5) > dataframe['ha_close'].shift(5))  # red bar
            )

        if 'CDLHAMMER' in params and params['CDLHAMMER']['enabled']:
            conditions.append(dataframe['CDLHAMMER'] >= 100)

        if 'CDLINVERTEDHAMMER' in params and params['CDLINVERTEDHAMMER']['enabled']:
            conditions.append(dataframe['CDLINVERTEDHAMMER'] == 100)

        if 'CDLDRAGONFLYDOJI' in params and params['CDLDRAGONFLYDOJI']['enabled']:
            conditions.append(dataframe['CDLDRAGONFLYDOJI'] == 100)

        if 'CDLPIERCING' in params and params['CDLPIERCING']['enabled']:
            conditions.append(dataframe['CDLPIERCING'] == 100)

        if 'CDLMORNINGSTAR' in params and params['CDLMORNINGSTAR']['enabled']:
            conditions.append(dataframe['CDLMORNINGSTAR'] == 100)

        if 'CDL3WHITESOLDIERS' in params and params['CDL3WHITESOLDIERS']['enabled']:
            conditions.append(dataframe['CDL3WHITESOLDIERS'] == 100)

        if 'CDL3LINESTRIKE' in params and params['CDL3LINESTRIKE']['enabled']:
            conditions.append(dataframe['CDL3LINESTRIKE'] == 100)

        if 'CDLSPINNINGTOP' in params and params['CDLSPINNINGTOP']['enabled']:
            conditions.append(dataframe['CDLSPINNINGTOP'] == 100)

        if 'CDLENGULFING' in params and params['CDLENGULFING']['enabled']:
            conditions.append(dataframe['CDLENGULFING'] == 100)

        if 'CDLHARAMI' in params and params['CDLHARAMI']['enabled']:
            conditions.append(dataframe['CDLHARAMI'] == 100)

        if 'CDL3OUTSIDE' in params and params['CDL3OUTSIDE']['enabled']:
            conditions.append(dataframe['CDL3OUTSIDE'] == 100)

        if 'CDL3INSIDE' in params and params['CDL3INSIDE']['enabled']:
            conditions.append(dataframe['CDL3INSIDE'] == 100)

        # TRIGGERS
        triggers = {
            'lower_bb': dataframe['tema'] <= dataframe['bb_lowerband'],
            'faststoch10': (crossed_above(dataframe['fastd'], 10.0)),
            'ao_cross_zero': (crossed_above(dataframe['ao'], 0.0)),
            'ema50_cross_ema100': (crossed_above(dataframe['ema50'], dataframe['ema100'])),
            'ema5_cross_ema10': (crossed_above(dataframe['ema5'], dataframe['ema10'])),
            'macd_cross_signal': (crossed_above(dataframe['macd'], dataframe['macdsignal'])),
            'sar_reversal': (crossed_above(dataframe['close'], dataframe['sar'])),
            'stochf_cross': (crossed_above(dataframe['fastk'], dataframe['fastd'])),
            'ht_sine': (crossed_above(dataframe['htleadsine'], dataframe['htsine'])),
            'cci_cross_100': (crossed_above(dataframe['cci'], 100.0)),
        }
        conditions.append(triggers.get(params['trigger']['type']))

        dataframe.loc[
            reduce(lambda x, y: x & y, conditions),
            'buy'] = 1

        return dataframe
    return populate_buy_trend
