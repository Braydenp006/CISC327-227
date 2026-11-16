# CISC327 Assignment 3 coverage-directed tests - Ali Senel (Member B)
# Area: app/routes/views.py (the HTML pages), which was only 37% covered at baseline.
from datetime import date

import pytest

from app import store


def add_equipment(client, name="Drill", category="Tools", total_units="2"):
    return client.post(
        "/ui/equipment",
        data={"name": name, "category": category, "total_units": total_units},
    )


def add_renter(client, name="Alice Smith", email="alice@example.com"):
    return client.post("/ui/renters", data={"name": name, "email": email})


# ---------- Home page ----------

def test_home_page_renders_links_to_each_section(client):
    res = client.get("/")
    assert res.status_code == 200
    body = res.get_data(as_text=True)
    assert "Equipment Rental Management" in body
    assert "/ui/equipment" in body
    assert "/ui/renters" in body
    assert "/ui/rentals" in body


# ---------- Equipment pages ----------

def test_equipment_page_lists_existing_equipment(client):
    add_equipment(client, "Ladder", "Tools", "3")
    res = client.get("/ui/equipment")
    assert res.status_code == 200
    body = res.get_data(as_text=True)
    assert "Ladder" in body
    assert "Tools" in body


def test_equipment_form_creates_item_with_all_units_available(client):
    res = add_equipment(client, "Drill", "Power Tools", "4")
    assert res.status_code == 302
    assert res.headers["Location"].endswith("/ui/equipment")
    item = store.equipment[1]
    assert item.name == "Drill"
    assert item.category == "Power Tools"
    assert item.total_units == 4
    assert item.available_units == 4


@pytest.mark.xfail(
    raises=ValueError,
    reason="Existing defect: equipment_page calls int() on total_units without "
    "validation, so a non-numeric value raises an unhandled ValueError (HTTP 500) "
    "instead of a 4xx rejection.",
)
def test_equipment_form_rejects_non_numeric_units(client):
    res = add_equipment(client, "Drill", "Tools", "many")
    assert res.status_code >= 400
    assert store.equipment == {}


def test_delete_equipment_page_removes_item(client):
    add_equipment(client, "Drill")
    res = client.post("/ui/equipment/1/delete")
    assert res.status_code == 302
    assert 1 not in store.equipment


def test_delete_equipment_page_unknown_id_changes_nothing(client):
    add_equipment(client, "Drill")
    res = client.post("/ui/equipment/999/delete")
    assert res.status_code == 302
    assert list(store.equipment) == [1]


# ---------- Renter pages ----------

def test_renters_form_creates_renter_and_page_lists_them(client):
    res = add_renter(client, "Bob Builder", "bob@example.com")
    assert res.status_code == 302
    assert res.headers["Location"].endswith("/ui/renters")
    assert store.renters[1].email == "bob@example.com"
    page = client.get("/ui/renters")
    assert page.status_code == 200
    assert "Bob Builder" in page.get_data(as_text=True)


def test_delete_renter_page_removes_renter(client):
    add_renter(client)
    res = client.post("/ui/renters/1/delete")
    assert res.status_code == 302
    assert 1 not in store.renters


def test_delete_renter_page_unknown_id_changes_nothing(client):
    add_renter(client)
    res = client.post("/ui/renters/999/delete")
    assert res.status_code == 302
    assert list(store.renters) == [1]


# ---------- Rental pages ----------

def test_rentals_page_checkout_creates_rental_and_reduces_stock(client):
    add_equipment(client, "Drill", total_units="2")
    add_renter(client)
    res = client.post("/ui/rentals", data={"equipment_id": "1", "renter_id": "1"})
    assert res.status_code == 302
    assert res.headers["Location"].endswith("/ui/rentals")
    assert store.equipment[1].available_units == 1
    rental = store.rentals[1]
    assert rental.equipment_id == 1
    assert rental.renter_id == 1
    assert rental.return_date is None
    assert rental.due_date > date.today()


def test_rentals_page_lists_rentals(client):
    add_equipment(client)
    add_renter(client)
    client.post("/ui/rentals", data={"equipment_id": "1", "renter_id": "1"})
    res = client.get("/ui/rentals")
    assert res.status_code == 200
    assert "Return" in res.get_data(as_text=True)


def test_rentals_page_checkout_unknown_equipment_creates_nothing(client):
    add_renter(client)
    res = client.post("/ui/rentals", data={"equipment_id": "42", "renter_id": "1"})
    assert res.status_code == 302
    assert store.rentals == {}


def test_rentals_page_checkout_blocked_when_no_units_left(client):
    add_equipment(client, "Drill", total_units="1")
    add_renter(client)
    client.post("/ui/rentals", data={"equipment_id": "1", "renter_id": "1"})
    client.post("/ui/rentals", data={"equipment_id": "1", "renter_id": "1"})
    assert len(store.rentals) == 1
    assert store.equipment[1].available_units == 0


def test_rentals_page_checkout_blocked_for_out_of_service_equipment(client):
    add_equipment(client, "Drill", total_units="2")
    add_renter(client)
    store.equipment[1].is_available = False
    client.post("/ui/rentals", data={"equipment_id": "1", "renter_id": "1"})
    assert store.rentals == {}
    assert store.equipment[1].available_units == 2


def test_return_rental_page_marks_returned_and_restores_stock(client):
    add_equipment(client, "Drill", total_units="2")
    add_renter(client)
    client.post("/ui/rentals", data={"equipment_id": "1", "renter_id": "1"})
    res = client.post("/ui/rentals/1/return")
    assert res.status_code == 302
    assert store.rentals[1].return_date == date.today()
    assert store.equipment[1].available_units == 2


def test_return_rental_page_twice_does_not_add_stock_twice(client):
    add_equipment(client, "Drill", total_units="2")
    add_renter(client)
    client.post("/ui/rentals", data={"equipment_id": "1", "renter_id": "1"})
    client.post("/ui/rentals/1/return")
    client.post("/ui/rentals/1/return")
    assert store.equipment[1].available_units == 2


def test_return_rental_page_unknown_rental_changes_nothing(client):
    add_equipment(client, total_units="2")
    res = client.post("/ui/rentals/999/return")
    assert res.status_code == 302
    assert store.equipment[1].available_units == 2


def test_return_rental_page_survives_deleted_equipment(client):
    add_equipment(client)
    add_renter(client)
    client.post("/ui/rentals", data={"equipment_id": "1", "renter_id": "1"})
    store.equipment.pop(1)
    res = client.post("/ui/rentals/1/return")
    assert res.status_code == 302
    assert store.rentals[1].return_date == date.today()
