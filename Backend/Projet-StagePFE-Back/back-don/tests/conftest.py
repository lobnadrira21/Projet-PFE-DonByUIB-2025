
import os, sys, types, pytest

# En mode test
os.environ["UNIT_TEST"] = "1"

# ---------- Stubs ML (transformers / torch / facenet) ----------
if "transformers" not in sys.modules:
    t = types.ModuleType("transformers")

    class _Dummy:
        @classmethod
        def from_pretrained(cls, *a, **k): return cls()
        def __call__(self, *a, **k): return {}
        def to(self, *a, **k): return self
        def eval(self, *a, **k): return self
        def encode_image(self, *a, **k): return []
        def get_text_features(self, *a, **k): return []
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
        def __call__(self, *args, **kwargs): return []

    class InceptionResnetV1:
        def __init__(self, *args, **kwargs): pass
        def to(self, *args, **kwargs): return self
        def eval(self, *args, **kwargs): return self

    f.MTCNN = MTCNN
    f.InceptionResnetV1 = InceptionResnetV1
    sys.modules["facenet_pytorch"] = f


# ---------- App et modèles ----------
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


# ---------- Configuration DB ----------
@pytest.fixture(scope="session", autouse=True)
def _configure_db_url():
    """
    Configure l'app pour PostgreSQL en test.
    Nécessite POSTGRES_TEST_URL défini dans l'environnement.
    Exemple :
      postgresql+psycopg2://postgres:postgres123@localhost:5432/gestiondonsdb_test
    """
    pg_url = os.getenv("POSTGRES_TEST_URL")
    if not pg_url:
        pytest.skip("POSTGRES_TEST_URL non défini (base de test obligatoire).")

    flask_app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=pg_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    flask_app.config.setdefault("JWT_SECRET_KEY", "test-secret-key")
    # Empêche tout envoi réel d'email pendant les tests (si Mail est configuré)
    flask_app.config["MAIL_SUPPRESS_SEND"] = True
    return pg_url


@pytest.fixture(scope="session")
def app(_configure_db_url):
    """
    Crée le schéma une fois par session.
    ATTENTION : ne fait pas de drop_all sur une base partagée !
    """
    ctx = flask_app.app_context()
    ctx.push()
    db.create_all()

    # Seed minimal (gouvernorat id=1 attendu par les tests)
    if Gouvernorat is not None:
        try:
            g = db.session.get(Gouvernorat, 1)
            if not g:
                g = Gouvernorat(id=1, nomGouvernorat="Tunis")
                db.session.add(g)
                db.session.commit()
        except Exception:
            db.session.rollback()

    try:
        yield flask_app
    finally:
        db.session.remove()
        # Pas de drop_all ici (sécurité sur base partagée)
        ctx.pop()


# ---------- Gestion transactionnelle ----------
from sqlalchemy.orm import scoped_session, sessionmaker, Session as SASession

@pytest.fixture(scope="function")
def db_session(app):
    """
    Transaction + savepoint par test.
    Chaque test rollback tout → pas de persistance.
    """
    engine = db.engine
    connection = engine.connect()
    outer_tx = connection.begin()

    # session liée à cette connexion
    SessionLocal = sessionmaker(bind=connection, future=True)
    scoped = scoped_session(SessionLocal)

    old_session = db.session
    db.session = scoped

    # begin_nested sur la SESSION (pas la connexion)
    db.session.begin_nested()

    # Redémarre un savepoint après chaque fin de transaction imbriquée
    @pytest.fixture(autouse=True)
    def _no_op():
        yield

    @SASession.event.listens_for(SASession, "after_transaction_end")
    def restart_savepoint(sess, trans):
        # On ne relance que pour notre session de test
        if sess is not db.session:
            return
        # Si on vient de terminer le nested, on le recrée
        if trans.nested and not trans._parent.nested:
            try:
                sess.begin_nested()
            except Exception:
                pass

    try:
        yield db.session
    finally:
        try:
            # rollback global
            if db.session.is_active:
                db.session.rollback()
        except Exception:
            pass
        db.session.close()
        scoped.remove()
        # rollback de la transaction externe & fermeture
        try:
            if outer_tx.is_active:
                outer_tx.rollback()
        except Exception:
            pass
        connection.close()
        db.session = old_session


# ---------- Fixtures client ----------
@pytest.fixture()
def client(app, db_session):
    return app.test_client()


# ---------- Helpers JWT & utilisateurs ----------
def _mk_user(email: str, role: str, password: str = "pass"):
    u = User(email=email.strip(), role=role, is_verified=True)  # utile si certaines routes vérifient
    if hasattr(u, "set_password"):
        u.set_password(password)
    elif hasattr(u, "password_hash"):
        u.password_hash = password
    db.session.add(u)
    db.session.flush()
    return u

def _token_for(user_id: int, role: str, email: str | None = None):
    if create_access_token is None:
        pytest.skip("flask_jwt_extended indisponible (JWT).")
    claims = {"role": role}
    if email:
        claims["email"] = email
    # IMPORTANT: identity doit être une chaîne
    return create_access_token(identity=str(user_id), additional_claims=claims)

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
