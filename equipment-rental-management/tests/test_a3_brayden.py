from datetime import date, timedelta
from unittest.mock import patch
from test_brayden import make_item, make_renter


def test_checkout_confirmation_sent(client, monkeypatch):
    monkeypatch.setattr(
        "app.routes.rentals..send_notification",
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
    assert response.get_json()["notification sent":True]
    assert len(client.get(f"/equipment/{item_id}")) == 1


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
    assert response.get_json()["notification sent":True]

    expected_subject = f"Checkout Confirmed: {item.name}"
    expected_message = f"Hello {renter.name}, your rental for {item.name} has been confirmed, due on {due}"
    mock_send.assert_called_once_with(renter.email, expected_subject, expected_message)
