from datetime import date, timedelta
from unittest.mock import patch
from test_brayden import make_item, make_renter
from app import store


def test_checkout_confirmation_sent(client, monkeypatch):
    monkeypatch.setattr(
        "app.routes.rentals.send_notification",
        lambda recipient, subject, message: True,
    )  # stub

    item = make_item(client, "Canoe", "Water", 2)
    item_id = item.get_json()["id"]

    renter = make_renter(client, "Mike", "Mike@123.com")
    renter_id = renter.get_json()["id"]

    response = client.post(
        "/rentals", json={"equipment_id": item_id, "renter_id": renter_id}
    )
    assert response.status_code == 201
    assert response.get_json()["notification_sent"] == True
    assert client.get(f"/equipment/{item_id}").get_json()["available_units"] == 1
    assert len(store.rentals) == 1


def test_checkout_confirmation_mock(client):

    item = make_item(client, "Canoe", "Water", 2)
    item_id = item.get_json()["id"]

    renter = make_renter(client, "Mike", "Mike@123.com")
    renter_id = renter.get_json()["id"]

    due = (date.today() + timedelta(days=7)).isoformat()

    with patch("app.routes.rentals.send_notification", return_value=True) as mock_send:
        response = client.post(
            "/rentals", json={"equipment_id": item_id, "renter_id": renter_id}
        )
    assert response.status_code == 201
    assert response.get_json()["notification_sent"] == True

    expected_subject = "Checkout Confirmed: Canoe"
    expected_message = (
        f"Hello Mike, your rental for Canoe has been confirmed, due on {due}"
    )
    mock_send.assert_called_once_with(
        "Mike@123.com", expected_subject, expected_message
    )


# +++++++++++++++++ missing equipment 404 tests +++++++++++++++++++++++++++++++++++


def test_missing_equipment_put_404(client):
    response = client.put("/equipment/99", json={"name": "nothing"})
    assert response.status_code == 404
    assert response.get_json() == {"error": "Equipment not found"}


def test_missing_equipment_delete_404(client):
    response = client.delete("/equipment/99")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Equipment not found"}


def test_missing_equipment_patch_404(client):
    response = client.patch("/equipment/99/status", json={"is_available": False})
    assert response.status_code == 404
    assert response.get_json() == {"error": "Equipment not found"}


def test_missing_equipment_get_404(client):
    response = client.get("/equipment/99/availability")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Equipment not found"}


# ++++++++++++++++++ missing webpage tests +++++++++++++++++++++++++


def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Equipment Rental Management" in response.data


def test_add_equipment_page(client):
    response = client.post(
        "/ui/equipment",
        data={"name": "Canoe", "category": "Water", "total_units": "3"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Canoe" in response.data
    assert store.equipment[1].total_units == 3


def test_delete_equipment_page(client):
    response = client.post(
        "/ui/equipment",
        data={"name": "Canoe", "category": "Water", "total_units": "3"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    response = client.post("/ui/equipment/1/delete", follow_redirects=True)

    assert b"Canoe" not in response.data
    assert 1 not in store.equipment


def test_add_renter_page(client):
    response = client.post(
        "/ui/renters",
        data={"name": "Mike", "email": "Mike@123.com"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Mike" in response.data
    assert store.renters[1].email == "Mike@123.com"


def test_delete_renter_page(client):
    response = client.post(
        "/ui/renters",
        data={"name": "Mike", "email": "Mike@123.com"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    response = client.post("/ui/renters/1/delete", follow_redirects=True)

    assert b"Mike" not in response.data
    assert 1 not in store.renters
