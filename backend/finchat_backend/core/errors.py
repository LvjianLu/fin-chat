"""Backend-specific error types."""


class BackendError(Exception):
    """Base backend error."""


class BackendConfigurationError(BackendError):
    """Raised when backend configuration is missing or invalid."""


class SessionNotFoundError(BackendError):
    """Raised when a session cannot be found."""


class SessionPersistenceError(BackendError):
    """Raised when session persistence operations fail."""


class DocumentProcessingError(BackendError):
    """Raised when document extraction or loading fails."""
