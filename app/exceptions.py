class TyreTrackerError(Exception):
    """Base class for errors the API turns into HTTP responses."""

class TyreNotFound(TyreTrackerError):
    pass