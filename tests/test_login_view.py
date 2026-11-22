from fastapi.testclient import TestClient
from sqlmodel import Session
from app.services import auth_service as AuthService


def test_login_page_renders(client: TestClient):
    res = client.get("/login")
    assert res.status_code == 200
    assert 'name="username"' in res.text
    assert "<nav>" not in res.text


def test_login_bad_credentials(client: TestClient):
    res = client.post("/login", data={"username": "nobody", "password": "wrongpass1"})
    assert res.status_code == 401
    assert "Invalid username or password" in res.text
    assert "access_token" not in res.cookies


def test_login_success_redirects_with_cookie(client: TestClient, session: Session):
    AuthService.create_user_account(session, "andy", "correct-horse-1")
    session.commit()
    res = client.post(
        "/login",
        data={"username": "Andy", "password": "correct-horse-1"},
        follow_redirects=False,
    )
    assert res.status_code == 303
    assert res.headers["location"] == "/"
    assert "access_token" in res.cookies
