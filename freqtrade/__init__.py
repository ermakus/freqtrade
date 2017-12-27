""" FreqTrade bot """
__version__ = '0.14.3'


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
    This happens whne trade requirements not met, i.e. 
    """
