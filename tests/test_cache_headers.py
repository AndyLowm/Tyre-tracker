from fastapi.testclient import TestClient


def test_html_pages_are_not_cached(client: TestClient):
    res = client.get("/login")
    assert res.headers["cache-control"] == "no-store"


def test_json_responses_keep_default_caching(client: TestClient, tyre: dict):
    res = client.get(f"/tyre/check-stock/{tyre['tyre_id']}")
    assert res.status_code == 200
    assert "cache-control" not in res.headers


def test_htmx_history_cache_disabled(client: TestClient):
    res = client.get("/login")
    assert '"historyCacheSize": 0' in res.text
