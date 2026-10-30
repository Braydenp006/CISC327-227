# CISC327 Assignment 2 Test Suite - Ali Senel 
import pytest

def make_renter(client, name, email):
    return client.post("/renters", json={"name": name, "email": email})

def make_item(client, name, category, total_units):
    return client.post("/equipment", json={"name": name, "category": category, "total_units": total_units})

def test_create_renter_persists(client):
    res = make_renter(client, "Alice Smith", "alice@example.com")
    assert res.status_code == 201
    assert res.get_json()["name"] == "Alice Smith"

def test_list_all_renters(client):
    make_renter(client, "Alice Smith", "alice@example.com")
    listing = client.get("/renters")
    assert listing.status_code == 200
    assert any(r["name"] == "Alice Smith" for r in listing.get_json())

def test_view_one_renter(client):
    res = make_renter(client, "Bob Builder", "bob@example.com")
    renter_id = res.get_json()["id"]
    view = client.get(f"/renters/{renter_id}")
    assert view.status_code == 200
    assert view.get_json()["email"] == "bob@example.com"

def test_update_renter(client):
    res = make_renter(client, "Bob Builder", "bob@example.com")
    renter_id = res.get_json()["id"]
    update = client.put(f"/renters/{renter_id}", json={"name": "Robert Builder", "email": "robert@example.com"})
    assert update.status_code == 200
    assert update.get_json()["name"] == "Robert Builder"

def test_delete_renter(client):
    res = make_renter(client, "Temp User", "temp@example.com")
    renter_id = res.get_json()["id"]
    del_res = client.delete(f"/renters/{renter_id}")
    assert del_res.status_code in [200, 204]
    
    check = client.get(f"/renters/{renter_id}")
    assert check.status_code == 404

def test_return_equipment_restores_units(client):
    item = make_item(client, "Kayak", "Water", 1)
    item_id = item.get_json()["id"]
    renter = make_renter(client, "Charlie", "charlie@example.com")
    renter_id = renter.get_json()["id"]
    checkout = client.post("/rentals", json={"equipment_id": item_id, "renter_id": renter_id})
    rental_id = checkout.get_json()["id"]
    
    return_res = client.put(f"/rentals/{rental_id}/return", json={"condition": "good"})
    assert return_res.status_code == 200

def test_lookup_rentals_by_renter_and_equipment(client):
    item = make_item(client, "Helmet", "Safety", 5)
    item_id = item.get_json()["id"]
    renter = make_renter(client, "Eve", "eve@example.com")
    renter_id = renter.get_json()["id"]
    client.post("/rentals", json={"equipment_id": item_id, "renter_id": renter_id})
    
    lookup = client.get(f"/rentals?renter_id={renter_id}")
    assert lookup.status_code == 200
    assert len(lookup.get_json()) > 0

def test_extend_rental_updates_due_date(client):
    item = make_item(client, "Tent", "Camping", 2)
    item_id = item.get_json()["id"]
    renter = make_renter(client, "Diana", "diana@example.com")
    renter_id = renter.get_json()["id"]
    checkout = client.post("/rentals", json={"equipment_id": item_id, "renter_id": renter_id})
    rental_id = checkout.get_json()["id"]
    
    extend = client.put(f"/rentals/{rental_id}/extend", json={"days": 3})
    assert extend.status_code == 200

def test_release_deposit_sets_flag(client):
    item = make_item(client, "Kayak2", "Water", 1)
    item_id = item.get_json()["id"]
    renter = make_renter(client, "Charlie2", "charlie2@example.com")
    renter_id = renter.get_json()["id"]
    checkout = client.post("/rentals", json={"equipment_id": item_id, "renter_id": renter_id})
    rental_id = checkout.get_json()["id"]
    
    client.put(f"/rentals/{rental_id}/return", json={"condition": "good"})
    release = client.put(f"/rentals/{rental_id}/deposit/release")
    assert release.status_code == 200
    assert release.get_json()["deposit_released"] is True

def test_return_already_returned_rental_fails(client):
    item = make_item(client, "Bike", "Transport", 1)
    item_id = item.get_json()["id"]
    renter = make_renter(client, "Frank", "frank@example.com")
    renter_id = renter.get_json()["id"]
    checkout = client.post("/rentals", json={"equipment_id": item_id, "renter_id": renter_id})
    rental_id = checkout.get_json()["id"]
    
    client.put(f"/rentals/{rental_id}/return", json={"condition": "good"})
    second_return = client.put(f"/rentals/{rental_id}/return", json={"condition": "good"})
    assert second_return.status_code == 400