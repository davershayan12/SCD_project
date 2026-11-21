"""Custom exception classes."""


class ResearchRadarError(Exception):
    """Base exception for ResearchRadar errors."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(ResearchRadarError):
    """Raised when file validation fails."""

    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class FileProcessingError(ResearchRadarError):
    """Raised when file processing fails."""

    def __init__(self, message: str):
        super().__init__(message, status_code=422)


class NotFoundError(ResearchRadarError):
    """Raised when a resource is not found."""

    def __init__(self, message: str):
        super().__init__(message, status_code=404)


class AuthorizationError(ResearchRadarError):
    """Raised when user is not authorized."""

    def __init__(self, message: str):
        super().__init__(message, status_code=403)
