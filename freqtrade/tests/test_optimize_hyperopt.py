# pragma pylint: disable=missing-docstring,W0212

from freqtrade.optimize.hyperopt import calculate_loss, TARGET_TRADES, EXPECTED_MAX_PROFIT


def test_loss_calculation_prefer_correct_trade_count():
    correct = calculate_loss(1, TARGET_TRADES)
    over = calculate_loss(1, TARGET_TRADES + 100)
    under = calculate_loss(1, TARGET_TRADES - 100)
    assert over > correct
    assert under > correct


def test_loss_calculation_has_limited_profit():
    correct = calculate_loss(EXPECTED_MAX_PROFIT, TARGET_TRADES)
    over = calculate_loss(EXPECTED_MAX_PROFIT * 2, TARGET_TRADES)
    under = calculate_loss(EXPECTED_MAX_PROFIT / 2, TARGET_TRADES)
    assert over == correct
    assert under > correct
