from sqlmodel import Session
from app.services import tyre_service as TyreService


def test_get_total_stock(session: Session, tyre: dict):
    assert TyreService.get_total_stock(session, 1) == 5


def test_get_total_stock_is_account_isolated(session: Session, tyre: dict):
    assert TyreService.get_total_stock(session, 2) == 0
