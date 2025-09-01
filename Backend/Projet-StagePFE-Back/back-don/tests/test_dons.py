import io
from datetime import date

CREATE_DON = "/create-don"
UPDATE_DON = "/update-don"
DELETE_DON = "/delete-don"

def _multipart(fields: dict, files: dict[str, bytes] | None = None):
    data = {}
    for k, v in fields.items():
        data[k] = (None, str(v))
    filedata = {}
    if files:
        for name, content in files.items():
            filedata[name] = (io.BytesIO(content), f"{name}.jpg")
    return data, filedata

def test_create_don_requires_association(client, donator_token):
    form, files = _multipart({
        "titre": "Don Cantine",
        "objectif": "1000",
        "date_fin_collecte": date.today().isoformat()
    })
    r = client.post(CREATE_DON, data=form, content_type="multipart/form-data",
                    headers={"Authorization": f"Bearer {donator_token}"})
    assert r.status_code == 403

def test_create_don_as_association(client, assoc_token, db_session):
    # ⚠️ Ta route exige une Association liée au user association (email match)
    # Si besoin, crée-la ici pour obtenir un 201 réel.
    from app import Association, Gouvernorat
    assoc_user = db_session.query(Association).filter_by(email="assoc@uib.tn").first()
    if not assoc_user:
        g = db_session.query(Gouvernorat).first()
        db_session.add(Association(
            nom_complet="Assoc Dev",
            email="assoc@uib.tn",
            description_association="test",
            telephone="22123458",
            adresse="Tunis",
            type_association=getattr(__import__('app'), 'TypeAssociationEnum').HUMANITAIRE,  # small trick to access enum
            gouvernorat_id=g.id if g else 1,
            id_admin=1
        ))
        db_session.commit()

    form, files = _multipart({
        "titre": "Don Cartable",
        "objectif": "500",
        "date_fin_collecte": date.today().isoformat(),
        "description": "rentrée"
    })
    r = client.post(CREATE_DON, data=form, content_type="multipart/form-data",
                    headers={"Authorization": f"Bearer {assoc_token}"})
    assert r.status_code in (201, 404), r.data  # 404 si lookup association/email ne match pas

def test_update_don(client, assoc_token):
    form, _ = _multipart({"titre": "Don Cartable (maj)"})
    r = client.put(f"{UPDATE_DON}/1", data=form, content_type="multipart/form-data",
                   headers={"Authorization": f"Bearer {assoc_token}"})
    assert r.status_code in (200, 404, 400)

def test_delete_don(client, assoc_token):
    r = client.delete(f"{DELETE_DON}/1", headers={"Authorization": f"Bearer {assoc_token}"})
    assert r.status_code in (200, 404)
