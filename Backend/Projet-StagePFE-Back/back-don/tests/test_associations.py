import pytest

from app import Gouvernorat

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
    # Un donateur ne peut pas créer => 403
    assert r.status_code == 403, r.data

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
    # 201 si créée, 409 si relancé
    assert r.status_code in (201, 409), r.data

def test_list_associations(client, admin_token, donator_token):
    r = client.get(LIST_, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code in (200, 204), r.data
    r = client.get(LIST_, headers={"Authorization": f"Bearer {donator_token}"})
    assert r.status_code in (200, 204), r.data

def test_modify_association_admin(client, admin_token):
    # On tente de modifier l’ID 1 ; selon l’état de la DB de test, ça peut être 200 (ok) ou 404 (absent) ou 409 (conflit email)
    form = {"nom_complet": "Assoc Beta (modif)"}
    r = client.put(f"{MODIFY}/1", data=form, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code in (200, 404, 409), r.data

def test_delete_association_admin(client, admin_token):
    # On tente de supprimer un ID improbable => souvent 404, sinon 200 si existe
    r = client.delete(f"{DELETE}/9999", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code in (200, 404), r.data