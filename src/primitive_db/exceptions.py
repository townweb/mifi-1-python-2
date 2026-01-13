class DBError(Exception):
    """Base error for primitive_db."""


class ParseError(DBError):
    """Command parsing error."""


class ValidationError(DBError):
    """Input validation error."""


class NotFoundError(DBError):
    """Missing table/column error."""


class StorageError(DBError):
    """Read/write JSON or filesystem error."""
