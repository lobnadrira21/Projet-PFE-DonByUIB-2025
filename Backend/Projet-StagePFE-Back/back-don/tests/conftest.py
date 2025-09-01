# tests/conftest.py
import os, sys, types, pytest
os.environ["UNIT_TEST"] = "1"   # must be before importing app

if "transformers" not in sys.modules:
    t = types.ModuleType("transformers")

    class _Dummy:
        @classmethod
        def from_pretrained(cls, *a, **k): return cls()
        def __call__(self, *a, **k): return {}
        def to(self, *a, **k): return self
        def eval(self, *a, **k): return self
        # common names sometimes used:
        def encode_image(self, *a, **k): return []
        def get_text_features(self, *a, **k): return []
        # catch-all so any unexpected attr is a no-op
        def __getattr__(self, name):
            def _noop(*a, **k): return self
            return _noop

    t.CLIPProcessor = _Dummy
    t.CLIPModel = _Dummy
    sys.modules["transformers"] = t


if "torch" not in sys.modules:
    torch_stub = types.ModuleType("torch")
    class _Cuda:
        @staticmethod
        def is_available(): return False
    torch_stub.cuda = _Cuda()
    sys.modules["torch"] = torch_stub


if "facenet_pytorch" not in sys.modules:
    f = types.ModuleType("facenet_pytorch")

    class MTCNN:
        def __init__(self, *args, **kwargs): pass
        def __call__(self, *args, **kwargs): return []  # pretend no faces

    class InceptionResnetV1:
        def __init__(self, *args, **kwargs): pass
        def to(self, *args, **kwargs): return self
        def eval(self, *args, **kwargs): return self

    f.MTCNN = MTCNN
    f.InceptionResnetV1 = InceptionResnetV1
    sys.modules["facenet_pytorch"] = f


from app import app as flask_app
from app import db

try:
    from app import User, Association, Don, Gouvernorat, TypeAssociationEnum
except Exception:
    User = Association = Don = Gouvernorat = TypeAssociationEnum = None  

try:
    from flask_jwt_extended import create_access_token
except Exception:
    create_access_token = None

@pytest.fixture(scope="session", autouse=True)
def _configure_db_url():
    """
    Force l'app à utiliser PostgreSQL pour les tests.
    Défini via POSTGRES_TEST_URL. Exemple:
    postgresql+psycopg2://postgres:postgres123@localhost:5432/gestiondonsdb?client_encoding=utf8
    """
    pg_url = os.getenv("POSTGRES_TEST_URL")
    if not pg_url:
        pytest.skip("POSTGRES_TEST_URL non défini.")
    flask_app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=pg_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    return pg_url
@pytest.fixture(scope="session")
def app(_configure_db_url):
    """
    Crée le schéma une fois pour la session, puis applique un mécanisme
    de transaction/savepoint par test dans la fixture 'db_session'.
    """
    ctx = flask_app.app_context(); ctx.push()
    # Crée toutes les tables
    db.create_all()

    # Seed minimal (gouvernorat id=1) si nécessaire
    if Gouvernorat is not None:
        try:
            if Gouvernorat.query.count() == 0:
                g = Gouvernorat(nomGouvernorat="Tunis")
                db.session.add(g); db.session.commit()
        except Exception:
            db.session.rollback()

    try:
        yield flask_app
    finally:
        # Nettoyage final du schéma
        db.session.remove()
        db.drop_all()
        ctx.pop()

@pytest.fixture(scope="function")
def db_session(app):
    """
    Transaction/savepoint par test → aucune persistance après chaque test.
    """
    engine = db.engine
    conn = engine.connect()
    trans = conn.begin()  # transaction externe

    # attacher une session dédiée à cette connexion
    options = dict(bind=conn, binds={})
    sess = db.create_scoped_session(options=options)
    old_session = db.session
    db.session = sess

    nested = conn.begin_nested()  # savepoint

    from sqlalchemy import event
    @event.listens_for(sess(), "after_transaction_end")
    def _restart_savepoint(session, transaction):
        nonlocal nested
        if not nested.is_active:
            nested = conn.begin_nested()

    try:
        yield db.session
    finally:
        sess.remove()
        db.session = old_session
        nested.rollback()
        trans.rollback()
        conn.close()

@pytest.fixture()
def client(app, db_session):
    return app.test_client()

# ---------- Helpers JWT & users ----------
def _mk_user(email: str, role: str, password: str = "pass"):
    u = User(email=email.strip(), role=role)
    if hasattr(u, "set_password"):
        u.set_password(password)
    elif hasattr(u, "password_hash"):
        u.password_hash = password
    db.session.add(u)
    db.session.flush()  # pour avoir u.id
    return u

def _token_for(user_id: int, role: str, email: str | None = None):
    if create_access_token is None:
        pytest.skip("flask_jwt_extended indisponible (JWT).")
    claims = {"role": role}
    if email:
        claims["email"] = email
    return create_access_token(identity=user_id, additional_claims=claims)

@pytest.fixture()
def admin_token(db_session):
    admin = db.session.query(User).filter_by(role="admin").first() or _mk_user("admin@uib.tn", "admin")
    return _token_for(admin.id, "admin", admin.email)

@pytest.fixture()
def assoc_token(db_session):
    assoc = db.session.query(User).filter_by(role="association").first() or _mk_user("assoc@uib.tn", "association")
    return _token_for(assoc.id, "association", assoc.email)

@pytest.fixture()
def donator_token(db_session):
    don = db.session.query(User).filter_by(role="donator").first() or _mk_user("don@uib.tn", "donator")
    return _token_for(don.id, "donator", don.email)

def auth_hdr(token: str | None):
    return {} if not token else {"Authorization": f"Bearer {token}"}