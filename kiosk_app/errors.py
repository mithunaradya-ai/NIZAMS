"""Application-domain errors."""


class KioskError(Exception):
    """Base class for errors safe to map to kiosk responses."""


class BhashiniCallError(KioskError):
    """A Bhashini SDK call returned an SDK-formatted error string."""


class ProviderError(KioskError):
    """An LLM provider request or structured response failed."""


class SchemaMismatchError(KioskError):
    """A MongoDB document does not match the declared scheme contract."""
