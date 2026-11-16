# CISC327 Assignment 3 coverage-directed tests - Ali Senel (Member B)
# Areas (from Table A): app/routes/rentals.py, 404 paths in app/routes/renters.py,
# and rentals_page / return_rental_page in app/routes/views.py.
from datetime import date, timedelta

import pytest

from app import store


def make_renter(client, name="Alice Smith", email="alice@example.com"):
    return client.post("/renters", json={"name": name, "email": email}).get_json()


def make_item(client, name="Drill", total_units=2):
    return client.post(
        "/equipment",
        json={"name": name, "category": "Tools", "total_units": total_units},
    ).get_json()


def checkout(client, equipment_id, renter_id, **extra):
    return client.post(
        "/rentals",
        json={"equipment_id": equipment_id, "renter_id": renter_id, **extra},
    )


def make_rental(client, units=2):
    renter = make_renter(client)
    item = make_item(client, total_units=units)
    return checkout(client, item["id"], renter["id"]).get_json(), item, renter


# ---------- rentals.py: list filters ----------

def test_list_rentals_filters_by_equipment_id(client):
    renter = make_renter(client)
    drill = make_item(client, "Drill")
    saw = make_item(client, "Saw")
    checkout(client, drill["id"], renter["id"])
    checkout(client, saw["id"], renter["id"])
    res = client.get(f"/rentals?equipment_id={saw['id']}")
    assert res.status_code == 200
    rentals = res.get_json()
    assert len(rentals) == 1
    assert rentals[0]["equipment_id"] == saw["id"]


def test_list_rentals_filters_by_renter_and_equipment_together(client):
    alice = make_renter(client, "Alice", "a@example.com")
    bob = make_renter(client, "Bob", "b@example.com")
    drill = make_item(client, "Drill", 3)
    checkout(client, drill["id"], alice["id"])
    checkout(client, drill["id"], bob["id"])
    res = client.get(f"/rentals?renter_id={bob['id']}&equipment_id={drill['id']}")
    rentals = res.get_json()
    assert len(rentals) == 1
    assert rentals[0]["renter_id"] == bob["id"]


def test_list_rentals_equipment_filter_with_no_match_returns_empty_list(client):
    make_rental(client)
    res = client.get("/rentals?equipment_id=999")
    assert res.status_code == 200
    assert res.get_json() == []


# ---------- rentals.py: checkout errors ----------

def test_checkout_unknown_renter_returns_404_and_keeps_stock(client):
    item = make_item(client, total_units=2)
    res = checkout(client, item["id"], 999)
    assert res.status_code == 404
    assert res.get_json() == {"error": "Renter not found"}
    assert store.equipment[item["id"]].available_units == 2
    assert store.rentals == {}


# ---------- rentals.py: return ----------

def test_return_unknown_rental_returns_404(client):
    res = client.put("/rentals/999/return")
    assert res.status_code == 404
    assert res.get_json() == {"error": "Rental not found"}


def test_return_rental_sets_return_date_and_restores_stock(client):
    rental, item, _ = make_rental(client, units=2)
    res = client.put(f"/rentals/{rental['id']}/return")
    assert res.status_code == 200
    assert res.get_json()["return_date"] == date.today().isoformat()
    assert store.equipment[item["id"]].available_units == 2


# ---------- rentals.py: extend ----------

def test_extend_unknown_rental_returns_404(client):
    res = client.put("/rentals/999/extend", json={"days": 3})
    assert res.status_code == 404
    assert res.get_json() == {"error": "Rental not found"}


def test_extend_returned_rental_returns_400_and_keeps_due_date(client):
    rental, _, _ = make_rental(client)
    client.put(f"/rentals/{rental['id']}/return")
    due_before = store.rentals[rental["id"]].due_date
    res = client.put(f"/rentals/{rental['id']}/extend", json={"days": 3})
    assert res.status_code == 400
    assert res.get_json() == {"error": "Rental already returned"}
    assert store.rentals[rental["id"]].due_date == due_before


def test_extend_rental_moves_due_date_by_given_days(client):
    rental, _, _ = make_rental(client)
    due_before = store.rentals[rental["id"]].due_date
    res = client.put(f"/rentals/{rental['id']}/extend", json={"days": 3})
    assert res.status_code == 200
    assert store.rentals[rental["id"]].due_date == due_before + timedelta(days=3)


def test_extend_rental_defaults_to_one_day(client):
    rental, _, _ = make_rental(client)
    due_before = store.rentals[rental["id"]].due_date
    res = client.put(f"/rentals/{rental['id']}/extend", json={})
    assert res.status_code == 200
    assert store.rentals[rental["id"]].due_date == due_before + timedelta(days=1)


# ---------- rentals.py: deposit release ----------

def test_release_deposit_unknown_rental_returns_404(client):
    res = client.put("/rentals/999/deposit/release")
    assert res.status_code == 404
    assert res.get_json() == {"error": "Rental not found"}


def test_release_deposit_before_return_returns_400(client):
    rental, _, _ = make_rental(client)
    res = client.put(f"/rentals/{rental['id']}/deposit/release")
    assert res.status_code == 400
    assert res.get_json() == {"error": "Equipment has not been returned yet"}
    assert store.rentals[rental["id"]].deposit_released is False


@pytest.mark.xfail(
    reason="Existing defect: release_deposit returns deposit_released=true but never "
    "sets rental.deposit_released, so the change is not persisted.",
    strict=True,
)
def test_release_deposit_persists_released_flag(client):
    rental, _, _ = make_rental(client)
    client.put(f"/rentals/{rental['id']}/return")
    res = client.put(f"/rentals/{rental['id']}/deposit/release")
    assert res.status_code == 200
    assert res.get_json()["deposit_released"] is True
    assert store.rentals[rental["id"]].deposit_released is True


# ---------- renters.py: 404 paths ----------

def test_update_unknown_renter_returns_404(client):
    res = client.put("/renters/999", json={"name": "Ghost"})
    assert res.status_code == 404
    assert res.get_json() == {"error": "Renter not found"}
    assert store.renters == {}


def test_delete_unknown_renter_returns_404_and_keeps_others(client):
    renter = make_renter(client)
    res = client.delete("/renters/999")
    assert res.status_code == 404
    assert res.get_json() == {"error": "Renter not found"}
    assert list(store.renters) == [renter["id"]]


# ---------- views.py: rentals pages ----------

def test_rentals_page_lists_rental_with_return_button(client):
    make_rental(client)
    res = client.get("/ui/rentals")
    assert res.status_code == 200
    assert "Return" in res.get_data(as_text=True)


def test_rentals_page_checkout_creates_rental_and_reduces_stock(client):
    renter = make_renter(client)
    item = make_item(client, total_units=2)
    res = client.post(
        "/ui/rentals",
        data={"equipment_id": str(item["id"]), "renter_id": str(renter["id"])},
    )
    assert res.status_code == 302
    assert res.headers["Location"].endswith("/ui/rentals")
    assert store.equipment[item["id"]].available_units == 1
    rental = store.rentals[1]
    assert rental.equipment_id == item["id"]
    assert rental.renter_id == renter["id"]
    assert rental.return_date is None
    assert rental.due_date > date.today()


def test_rentals_page_checkout_unknown_equipment_creates_nothing(client):
    renter = make_renter(client)
    res = client.post(
        "/ui/rentals", data={"equipment_id": "42", "renter_id": str(renter["id"])}
    )
    assert res.status_code == 302
    assert store.rentals == {}


def test_rentals_page_checkout_blocked_when_no_units_left(client):
    renter = make_renter(client)
    item = make_item(client, total_units=1)
    form = {"equipment_id": str(item["id"]), "renter_id": str(renter["id"])}
    client.post("/ui/rentals", data=form)
    client.post("/ui/rentals", data=form)
    assert len(store.rentals) == 1
    assert store.equipment[item["id"]].available_units == 0


def test_rentals_page_checkout_blocked_for_out_of_service_equipment(client):
    renter = make_renter(client)
    item = make_item(client, total_units=2)
    store.equipment[item["id"]].is_available = False
    client.post(
        "/ui/rentals",
        data={"equipment_id": str(item["id"]), "renter_id": str(renter["id"])},
    )
    assert store.rentals == {}
    assert store.equipment[item["id"]].available_units == 2


def test_return_rental_page_marks_returned_and_restores_stock(client):
    rental, item, _ = make_rental(client, units=2)
    res = client.post(f"/ui/rentals/{rental['id']}/return")
    assert res.status_code == 302
    assert store.rentals[rental["id"]].return_date == date.today()
    assert store.equipment[item["id"]].available_units == 2


def test_return_rental_page_twice_does_not_add_stock_twice(client):
    rental, item, _ = make_rental(client, units=2)
    client.post(f"/ui/rentals/{rental['id']}/return")
    client.post(f"/ui/rentals/{rental['id']}/return")
    assert store.equipment[item["id"]].available_units == 2


def test_return_rental_page_unknown_rental_changes_nothing(client):
    item = make_item(client, total_units=2)
    res = client.post("/ui/rentals/999/return")
    assert res.status_code == 302
    assert store.equipment[item["id"]].available_units == 2


def test_return_rental_page_survives_deleted_equipment(client):
    rental, item, _ = make_rental(client)
    store.equipment.pop(item["id"])
    res = client.post(f"/ui/rentals/{rental['id']}/return")
    assert res.status_code == 302
    assert store.rentals[rental["id"]].return_date == date.today()
