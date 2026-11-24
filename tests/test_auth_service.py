import pytest
from sqlmodel import Session, select
from app.models import Account, User
from app.services import auth_service as AuthService
from app.exceptions import InvalidCredentialsError, SignUpError

PW = "correct-horse-1"


def test_create_user_account_returns_acc_id(session: Session):
    acc_id = AuthService.create_user_account(session, "andy", PW, PW)
    user = session.exec(select(User).where(User.username == "andy")).one()
    assert user.acc_id == acc_id


def test_create_user_account_password_mismatch(session: Session):
    with pytest.raises(SignUpError, match="Passwords do not match"):
        AuthService.create_user_account(session, "andy", PW, "different-pass-2")
    assert session.exec(select(Account)).first() is None


def test_create_user_account_duplicate_username(session: Session):
    AuthService.create_user_account(session, "andy", PW, PW)
    with pytest.raises(SignUpError, match="Sign up failed"):
        AuthService.create_user_account(session, "Andy ", PW, PW)


def test_create_user_account_race_hits_unique_constraint(session: Session, monkeypatch):
    """Two sign-ups both pass the username check; the DB constraint must still stop the second."""
    AuthService.create_user_account(session, "racer", PW, PW)
    session.commit()
    monkeypatch.setattr(AuthService, "username_taken", lambda *_: False)
    with pytest.raises(SignUpError, match="Sign up failed"):
        AuthService.create_user_account(session, "racer", PW, PW)
    session.rollback()
    assert len(session.exec(select(User)).all()) == 1
    assert len(session.exec(select(Account)).all()) == 1


def test_verify_user_returns_acc_id(session: Session):
    acc_id = AuthService.create_user_account(session, "andy", PW, PW)
    assert AuthService.verify_user(session, "Andy", PW) == acc_id


def test_verify_user_unknown_user(session: Session):
    with pytest.raises(InvalidCredentialsError):
        AuthService.verify_user(session, "nobody", PW)


def test_verify_user_wrong_password(session: Session):
    AuthService.create_user_account(session, "andy", PW, PW)
    with pytest.raises(InvalidCredentialsError):
        AuthService.verify_user(session, "andy", "wrong-pass-9")
