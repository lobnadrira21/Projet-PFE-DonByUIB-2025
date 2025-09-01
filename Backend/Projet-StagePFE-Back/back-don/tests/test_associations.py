import pytest

CREATE = "/create-association"
LIST_  = "/associations"
MODIFY = "/modify-compte-association"
DELETE = "/delete-compte-association"
DETAIL = "/association"
GET_ME = "/get-profile-association"

def test_create_association_requires_admin(client, donator_token):
    payload = {
        "nom_complet": "Assoc Alpha",
        "email": "alpha@assoc.tn",
        "telephone": "22123456",
        "adresse": "Tunis",
        "type_association": "humanitaire",
        "password": "secret",
        "gouvernorat_id": 1
    }
    r = client.post(CREATE, json=payload, headers={"Authorization": f"Bearer {donator_token}"})
    assert r.status_code == 403

def test_create_association_ok_admin(client, admin_token):
    payload = {
        "nom_complet": "Assoc Beta",
        "email": "beta@assoc.tn",
        "telephone": "22123457",
        "adresse": "Ariana",
        "type_association": "humanitaire",
        "password": "secret",
        "gouvernorat_id": 1
    }
    r = client.post(CREATE, json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code in (201, 409), r.data  # 409 si déjà créée

def test_list_associations(client, admin_token, donator_token):
    r = client.get(LIST_, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code in (200, 204)
    r = client.get(LIST_, headers={"Authorization": f"Bearer {donator_token}"})
    assert r.status_code in (200, 204)

def test_modify_association_admin(client, admin_token):
    form = {"nom_complet": "Assoc Beta (modif)"}
    r = client.put(f"{MODIFY}/1", data=form, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code in (200, 404, 409)

def test_delete_association_admin(client, admin_token):
    r = client.delete(f"{DELETE}/9999", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code in (200, 404)
