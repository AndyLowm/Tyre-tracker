from fastapi.testclient import TestClient

def test_remove_stock_update_total(client: TestClient, tyre: dict):
    payload = {
        "location_amount": {
            "unit": 1
        }
    }
    res = client.patch(url=f'/tyre/remove-stock/{tyre["tyre_id"]}', json=payload)
    assert res.status_code == 200
    assert res.json()["total_stock"] == 4
    assert res.json()["stock_locations"]["unit"] == 0
    assert res.json()["stock_locations"]["van"] == 4

def test_not_enough_stock(client: TestClient, tyre: dict):
    payload = {
        "location_amount": {
            "unit": 4
        }
    }
    res = client.patch(url=f'/tyre/remove-stock/{tyre["tyre_id"]}', json=payload)
    assert res.status_code == 400
    assert "Not enough stock" in res.json()["detail"]

    check = client.get(url=f"/tyre/check-stock/{tyre["tyre_id"]}").json()["total_stock"]
    assert check == 5

def test_remove_unknown_location(client: TestClient, tyre: dict):
    payload = {
        "location_amount": {
            "unit2": 4
        }
    }
    res = client.patch(url=f'/tyre/remove-stock/{tyre["tyre_id"]}', json=payload)
    assert res.status_code == 400
def test_remove_stock_unknown_tyre(client: TestClient):
    res = client.patch("/tyre/remove-stock/999", json={"location_amount": {"unit": 1}})
    assert res.status_code == 404


def test_remove_negative_amount_rejected(client: TestClient, tyre: dict):
    res = client.patch(
        f'/tyre/remove-stock/{tyre["tyre_id"]}',
        json={"location_amount": {"unit": -5}},
    )
    assert res.status_code == 422


def test_remove_all_stock_from_location(client: TestClient, tyre: dict):
    res = client.patch(
        f'/tyre/remove-stock/{tyre["tyre_id"]}',
        json={"location_amount": {"van": 4}},
    )
    assert res.status_code == 200
    assert res.json()["stock_locations"]["van"] == 0
    assert res.json()["total_stock"] == 1


def test_remove_from_two_locations(client: TestClient, tyre: dict):
    res = client.patch(
        f'/tyre/remove-stock/{tyre["tyre_id"]}',
        json={"location_amount": {"unit": 1, "van": 2}},
    )
    assert res.status_code == 200
    assert res.json()["stock_locations"] == {"unit": 0, "van": 2}
    assert res.json()["total_stock"] == 2


def test_failed_removal_changes_nothing(client: TestClient, tyre: dict):
    # unit is valid, van is not: the whole request must be rejected
    res = client.patch(
        f'/tyre/remove-stock/{tyre["tyre_id"]}',
        json={"location_amount": {"unit": 1, "van": 99}},
    )
    assert res.status_code == 400

    check = client.get(f'/tyre/check-stock/{tyre["tyre_id"]}').json()
    assert check["stock_locations"] == {"unit": 1, "van": 4}
    assert check["total_stock"] == 5