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
    id = item.get_json()["id"]

    # test that indivdual item can be searched by item id
    response = client.get(f"/equipment/{id}")
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
    id = item.get_json()["id"]

    # change the name of the item
    response = client.put(f"/equipment/{id}", json={"name": "changed"})
    assert response.status_code == 200

    # check if change persists
    assert client.get(f"/equipment/{id}").get_json()["name"] == "changed"

    # check if change affected other fields like category
    assert client.get(f"/equipment/{id}").get_json()["category"] == "Water"


# Test 5 - delete equipment
def test_delete_equipment(client):
    # create items
    item = client.post(
        "/equipment",
        json={"name": "Life Jacket", "category": "Water", "total_units": 3},
    )
    assert item.status_code == 201
    id = item.get_json()["id"]

    # delete the item
    response = client.delete(f"/equipment/{id}")
    assert response.status_code == 204

    # check that value does not exist
    response = client.get(f"/equipment/{id}")
    assert response.status_code == 404


# Test 6 - set out of service
def test_set_out_of_service(client):
    pass
