# TEST 1 - Add equipment
def test_add_equipment_persists(client):
    response = client.post(
        "/equipment",
        json={"name": "Life Jacket", "category": "Water", "total_units": 3},
    )
    assert response.status_code == 201
    item = response.get_json()

    assert item["available_units"] == 3  # test if available_units saves
    # test if item iteself test_add_equipment_persists
    assert client.get(f"/equipment/{item['id']}").get_json()["name"] == "Life Jacket"


# Test 2 - listing equipment
def test_list_all_equipment(client):
    # create items
    item1 = client.post(
        "/equipment",
        json={"name": "Life Jacket", "category": "Water", "total_units": 3},
    )
    assert item1.status_code == 201
    item2 = client.post(
        "/equipment",
        json={"name": "Tent", "category": "Camping", "total_units": 1},
    )
    assert item2.status_code == 201

    # get the list
    response = client.get("/equipment")
    assert response.status_code == 200

    items = response.get_json()
    assert len(items) == 2


# Test 3 - viewing individual item
def test_view_one_item(client):
    # create items
    item = client.post(
        "/equipment",
        json={"name": "Life Jacket", "category": "Water", "total_units": 3},
    )
    assert item.status_code == 201
    item_id = item.get_json()["id"]

    # test that indivdual item can be searched by item id
    response = client.get(f"/equipment/{item_id}")
    assert response.status_code == 200
    assert response.get_json()["name"] == "Life Jacket"

    # check for non-existent equipment
    response = client.get("/equipment/99999")
    assert response.status_code == 404


# Test 4 - update equipment
def test_update_equipment(client):
    # create items
    item = client.post(
        "/equipment",
        json={"name": "Life Jacket", "category": "Water", "total_units": 3},
    )
    assert item.status_code == 201
    item_id = item.get_json()["id"]

    # change the name of the item
    response = client.put(f"/equipment/{item_id}", json={"name": "changed"})
    assert response.status_code == 200

    # check if change persists
    assert client.get(f"/equipment/{item_id}").get_json()["name"] == "changed"

    # check if change affected other fields like category
    assert client.get(f"/equipment/{item_id}").get_json()["category"] == "Water"


# Test 5 - delete equipment
def test_delete_equipment(client):
    # create items
    item = client.post(
        "/equipment",
        json={"name": "Life Jacket", "category": "Water", "total_units": 3},
    )
    assert item.status_code == 201
    item_id = item.get_json()["id"]

    # delete the item
    response = client.delete(f"/equipment/{item_id}")
    assert response.status_code == 204

    # check that value does not exist
    response = client.get(f"/equipment/{item_id}")
    assert response.status_code == 404


# Test 6 - set out of service
def test_set_out_of_service(client):
    # create items
    item = client.post(
        "/equipment",
        json={"name": "Life Jacket", "category": "Water", "total_units": 3},
    )
    assert item.status_code == 201
    item_id = item.get_json()["id"]

    # test out of service flag
    response = client.patch(
        f"/equipment/{item_id}/status", json={"is_available": False}
    )
    assert response.status_code == 200

    item = client.get(f"/equipment/{item_id}")
    assert item.get_json()["is_available"] == False


# test 7 - Check equipment availability
def test_check_equipment_availability(client):
    # create items
    item = client.post(
        "/equipment",
        json={"name": "Life Jacket", "category": "Water", "total_units": 1},
    )
    assert item.status_code == 201
    item_id = item.get_json()["id"]
    # create renter
    renter = client.post(
        "/renters",
        json={
            "name": "Ryan",
            "email": "ryan@whatevermail.com",
        },
    )
    assert renter.status_code == 201
    renter_id = renter.get_json()["id"]

    # check if is available returns True when it should
    avail = client.get(f"/equipment/{item_id}/availability")
    assert avail.get_json()["is_available"] is True

    # checkout to test if chekcing out changes available_units
    checkout = client.post(
        "/rentals", json={"equipment_id": item_id, "renter_id": renter_id}
    )
    assert checkout.status_code == 201

    client.patch(f"/equipment/{item_id}/status", json={"is_available": False})
    avail = client.get(f"/equipment/{item_id}/availability")

    assert avail.get_json()["available_units"] == 0
    assert avail.get_json()["total_units"] == 1

    # check if is available returns False when it should
    assert avail.get_json()["is_available"] is False


# Test 8 - Check out equipment
def test_check_out_equipment(client):
    # create items
    item = client.post(
        "/equipment",
        json={"name": "Life Jacket", "category": "Water", "total_units": 3},
    )
    assert item.status_code == 201
    item_id = item.get_json()["id"]

    # create renter``
    renter = client.post(
        "/renters",
        json={
            "name": "Ryan",
            "email": "ryan@whatevermail.com",
        },
    )
    assert renter.status_code == 201
    renter_id = renter.get_json()["id"]

    checkout = client.post(
        "/rentals", json={"equipment_id": item_id, "renter_id": renter_id}
    )
    assert checkout.status_code == 201
    # check if the rental got the correct informaiton
    rental = checkout.get_json()
    assert rental["equipment_id"] == item_id
    assert rental["renter_id"] == renter_id
    assert rental["return_date"] is None

    # test if checkout changed item's values
    item = client.get(f"/equipment/{item_id}")
    assert item.get_json()["available_units"] == 2
