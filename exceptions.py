# define Python user-defined exceptions
class CustomException(Exception):
    """Base class for other exceptions"""
    pass


class RuleNotSafeError(CustomException):
    """Raised when a rule is not safe"""
    pass
