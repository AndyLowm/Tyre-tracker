from fastapi.testclient import TestClient


def test_logout_clears_cookie_and_redirects(client: TestClient):
    res = client.post("/logout", follow_redirects=False)
    assert res.status_code == 303
    assert res.headers["location"] == "/login"
    cookie = res.headers["set-cookie"]
    assert cookie.startswith("access_token=")
    assert "Max-Age=0" in cookie
