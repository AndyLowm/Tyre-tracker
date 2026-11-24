from fastapi import status


class TyreTrackerError(Exception):
    """Base class for errors the API turns into HTTP responses."""
    status_code = status.HTTP_400_BAD_REQUEST

class TyreNotFoundError(TyreTrackerError):
    status_code = status.HTTP_404_NOT_FOUND

class StockError(TyreTrackerError):
    pass

class LocationError(TyreTrackerError):
    pass

class InvalidCredentialsError(TyreTrackerError):
    status_code = status.HTTP_401_UNAUTHORIZED

class SignUpError(TyreTrackerError):
    pass
