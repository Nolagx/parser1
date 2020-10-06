# define Python user-defined exceptions
class CustomException(Exception):
    """Base class for other exceptions"""
    pass


class RuleNotSafeError(CustomException):
    """Raised when a rule is not safe"""
    pass


class TermsNotProperlyTypedError(CustomException):
    """Raised when a term type in a term sequence does not match the schema's attribute type on the same index"""
    pass
