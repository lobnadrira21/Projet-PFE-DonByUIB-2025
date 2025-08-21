import pytest
from app import app as flask_app  # adapte si tu utilises une factory "create_app()"

@pytest.fixture()
def app():
    # Si tu as create_app(), fais: app = create_app(testing=True)
    flask_app.config.update({
        "TESTING": True,
    })
    yield flask_app

@pytest.fixture()
def client(app):
    return app.test_client()