import pytest

def make_renter(client, name, email):
    return client.post("/renters", json={"name": name, "email": email})

def make_item(client, name, category, total_units):
    return client.post("/equipment", json={"name": name, "category": category, "total_units": total_units})

def test_create_and_list_renters(client):
    res = make_renter(client, "Alice Smith", "alice@example.com")
    assert res.status_code == 201
    data = res.get_json()
    assert data["name"] == "Alice Smith"
    
    listing = client.get("/renters")
    assert listing.status_code == 200
    assert any(r["name"] == "Alice Smith" for r in listing.get_json())

def test_view_and_update_renter(client):
    res = make_renter(client, "Bob Builder", "bob@example.com")
    renter_id = res.get_json()["id"]

    view = client.get(f"/renters/{renter_id}")
    assert view.status_code == 200
    assert view.get_json()["email"] == "bob@example.com"

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

def test_return_equipment_and_deposit_release(client):
    item = make_item(client, "Kayak", "Water", 1)
    item_id = item.get_json()["id"]

    renter = make_renter(client, "Charlie", "charlie@example.com")
    renter_id = renter.get_json()["id"]

    checkout = client.post("/rentals", json={"equipment_id": item_id, "renter_id": renter_id})
    assert checkout.status_code == 201
    rental_id = checkout.get_json()["id"]

    # Return equipment
    return_res = client.put(f"/rentals/{rental_id}/return", json={"condition": "good"})
    assert return_res.status_code == 200

    # Release deposit
    release = client.put(f"/rentals/{rental_id}/deposit/release")
    assert release.status_code == 200
    assert release.get_json()["deposit_released"] is True

def test_extend_rental(client):
    item = make_item(client, "Tent", "Camping", 2)
    item_id = item.get_json()["id"]

    renter = make_renter(client, "Diana", "diana@example.com")
    renter_id = renter.get_json()["id"]

    checkout = client.post("/rentals", json={"equipment_id": item_id, "renter_id": renter_id})
    rental_id = checkout.get_json()["id"]

    extend = client.put(f"/rentals/{rental_id}/extend", json={"days": 3})
    assert extend.status_code == 200