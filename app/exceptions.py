class TyreTrackerError(Exception):
    """Base class for errors the API turns into HTTP responses."""

class TyreNotFoundError(TyreTrackerError):
    pass

class StockError(TyreTrackerError):
    pass

class LocationError(TyreTrackerError):
    pass