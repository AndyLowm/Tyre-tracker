from fastapi.testclient import TestClient

def test_add_new_stock_update_total(client: TestClient, tyre: dict):
    payload = {
        "location_amount":{
            "unit": 4
        },
        "cost_price": 10
    }
    res = client.patch(url=f"/tyre/add-stock/{tyre["tyre_id"]}", json=payload)
    assert res.status_code == 202
    assert res.json()["total_stock"] == 9
    assert res.json()["cost_price"] == 32.22

def test_add_stock_to_new_location_updates_total(client: TestClient, tyre: dict):
    res = client.patch(
        f"/tyre/add-stock/{tyre['tyre_id']}",
        json={"location_amount": {"garage": 2}, "cost_price": 50},
    )
    assert res.status_code == 202
    assert res.json()["total_stock"] == 7  