class DocumensoError(Exception):
    """Base exception for all Documenso integration errors."""


class DocumensoConfigurationError(DocumensoError):
    """Raised when Documenso integration is misconfigured."""


class DocumensoAuthenticationError(DocumensoError):
    """Raised when Documenso API authentication fails."""


class DocumensoRequestError(DocumensoError):
    """Raised when an HTTP request to Documenso fails."""


class DocumensoApiError(DocumensoError):
    """Raised when Documenso API returns an error response."""
