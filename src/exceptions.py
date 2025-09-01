"""Custom exceptions for the application."""


class DocumentError(Exception):
    """Base class for document-related errors."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class DocumentNotFoundError(DocumentError):
    """Raised when a document is not found."""

    def __init__(self, message: str):
        super().__init__(message, status_code=404)


class InvalidDocumentError(DocumentError):
    """Raised when a document is invalid (wrong type, size, etc)."""

    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class SummarizationError(DocumentError):
    """Raised when text summarization fails."""

    def __init__(self, message: str):
        super().__init__(message, status_code=500)
