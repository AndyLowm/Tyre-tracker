from fastapi.testclient import TestClient
from sqlmodel import Session, select
from app.models import User


def _post(client: TestClient, username="newuser", password="correct-horse-1", confirm=None):
    return client.post(
        "/signup",
        data={
            "username": username,
            "password": password,
            "confirm_password": confirm if confirm is not None else password,
        },
        follow_redirects=False,
    )


def test_signup_page_renders(client: TestClient):
    res = client.get("/signup")
    assert res.status_code == 200
    assert 'name="confirm_password"' in res.text
    assert "<nav>" not in res.text


def test_signup_success_redirects_and_can_login(client: TestClient, session: Session):
    res = _post(client)
    assert res.status_code == 303
    assert res.headers["location"] == "/"
    assert "access_token" in res.cookies
    assert session.exec(select(User).where(User.username == "newuser")).first()
    client.cookies.clear()
    res = client.post(
        "/login",
        data={"username": "newuser", "password": "correct-horse-1"},
        follow_redirects=False,
    )
    assert res.status_code == 303


def test_signup_password_mismatch(client: TestClient, session: Session):
    res = _post(client, confirm="different-pass-2")
    assert res.status_code == 400
    assert "Passwords do not match" in res.text
    assert session.exec(select(User)).first() is None


def test_signup_schema_validation(client: TestClient, session: Session):
    res = _post(client, password="short")
    assert res.status_code == 422
    assert "password 8-128" in res.text
    assert session.exec(select(User)).first() is None


def test_signup_duplicate_username(client: TestClient, session: Session):
    assert _post(client).status_code == 303
    res = _post(client, username="NewUser ")
    assert res.status_code == 400
    assert "Sign up failed" in res.text
    assert len(session.exec(select(User)).all()) == 1
