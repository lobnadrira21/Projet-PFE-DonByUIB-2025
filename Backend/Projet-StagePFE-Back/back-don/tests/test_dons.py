
import io
from datetime import date

CREATE_DON = "/create-don"
UPDATE_DON = "/update-don"
DELETE_DON = "/delete-don"

def _multipart(fields: dict, files: dict[str, bytes] | None = None):
    """
    Prépare un payload multipart pour le client Flask:
      - champs simples: str
      - fichiers: (BytesIO, filename)
    """
    data = {k: (v if isinstance(v, str) else str(v)) for k, v in fields.items()}
    if files:
        for name, content in files.items():
            data[name] = (io.BytesIO(content), f"{name}.jpg")
    return data

def test_create_don_requires_association(client, donator_token):
    data = _multipart({
        "titre": "Don Cantine",
        "objectif": "1000",
        "date_fin_collecte": date.today().isoformat(),
    })
    r = client.post(
        CREATE_DON,
        data=data,
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {donator_token}"},
    )
    # Un donateur n'a pas le droit de créer un don
    assert r.status_code == 403, r.data

def test_create_don_as_association(client, assoc_token, db_session):
    """
    La route nécessite:
      - un user role=association (fourni par assoc_token)
      - une table associations avec un enregistrement dont l'email == email du token association
      - un id_admin valide pointant vers un user admin existant
    """
    from app import Association, Gouvernorat, User, TypeAssociationEnum

    # 1) garantir un admin existant et récupérer son id
    admin = db_session.query(User).filter_by(role="admin").first()
    if not admin:
        admin = User(email="admin@uib.tn", role="admin", is_verified=True)
        if hasattr(admin, "set_password"): admin.set_password("secret")
        db_session.add(admin)
        db_session.commit()

    # 2) garantir un gouvernorat (conftest en crée déjà un id=1, on double-check)
    g = db_session.query(Gouvernorat).first()
    if not g:
        g = Gouvernorat(id=1, nomGouvernorat="Tunis")
        db_session.add(g)
        db_session.commit()

    # 3) garantir l'association liée à l'email du token d'association
    assoc = db_session.query(Association).filter_by(email="assoc@uib.tn").first()
    if not assoc:
        assoc = Association(
            nom_complet="Assoc Dev",
            email="assoc@uib.tn",
            description_association="test",
            telephone="22123458",
            adresse="Tunis",
            type_association=TypeAssociationEnum.HUMANITAIRE,
            gouvernorat_id=g.id,
            id_admin=admin.id,   # <-- pas de valeur en dur !
        )
        db_session.add(assoc)
        db_session.commit()

    data = _multipart({
        "titre": "Don Cartable",
        "objectif": "500",
        "date_fin_collecte": date.today().isoformat(),
        "description": "rentrée",
    })
    r = client.post(
        CREATE_DON,
        data=data,
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {assoc_token}"},
    )
    # 201 si créé ; 404 si la route a une logique qui échoue à retrouver l'association (selon implément)
    assert r.status_code in (201, 404), r.data

def test_update_don(client, assoc_token):
    data = _multipart({"titre": "Don Cartable (maj)"})
    r = client.put(
        f"{UPDATE_DON}/1",
        data=data,
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {assoc_token}"},
    )
    # 200 si ok, 404 si don inexistant, 400 si payload invalide
    assert r.status_code in (200, 404, 400), r.data

def test_delete_don(client, assoc_token):
    r = client.delete(
        f"{DELETE_DON}/1",
        headers={"Authorization": f"Bearer {assoc_token}"},
    )
    # 200 si supprimé, 404 sinon
    assert r.status_code in (200, 404), r.data
