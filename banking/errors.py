"""Exceptions shared by the service layer, the CLI and the GUI."""


class BankingError(Exception):
    """Base class for every error the user should see as a friendly message."""


class ValidationError(BankingError):
    """Input was missing or in the wrong format."""


class NotFoundError(BankingError):
    """A user or account id does not exist."""


class InsufficientFundsError(BankingError):
    """A withdrawal or transfer exceeds the available balance."""


class DatabaseError(BankingError):
    """MySQL could not be reached or returned an error."""
