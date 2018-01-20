""" FreqTrade bot """
__version__ = '0.15.1'


class DependencyException(BaseException):
    """
    Indicates that a assumed dependency is not met.
    This could happen when there is currently not enough money on the account.
    """


class OperationalException(BaseException):
    """
    Requires manual intervention.
    This happens when an exchange returns an unexpected error during runtime.
    """


class TradeException(BaseException):
    """
    Market should be blacklisted
    This happens when trade requirements not met, i.e. MIN_TRADE_REQUIREMENT_NOT_MET
    """
