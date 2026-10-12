"""Provider failures, independent of HTTP and FastAPI."""


class ProviderError(Exception):
    """Upstream unavailable or returned an invalid response."""


class ProviderUnavailableError(ProviderError):
    """The upstream is temporarily unavailable."""


class ProviderTimeoutError(ProviderUnavailableError):
    """The upstream request exceeded its timeout."""


class ProviderNotFoundError(ProviderError):
    """The requested resource does not exist in the provider's scope."""
