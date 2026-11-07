"""User-safe storage failures."""


class StorageError(RuntimeError):
    """A database operation failed; the HTTP layer returns a generic message."""
