# tests/conftest.py
import os, sys, types
os.environ["UNIT_TEST"] = "1"   # must be before importing app

# CI stub so 'from transformers import ...' doesn't explode
if "transformers" not in sys.modules:
    t = types.ModuleType("transformers")
    class _Dummy: pass
    t.CLIPProcessor = _Dummy
    t.CLIPModel = _Dummy
    sys.modules["transformers"] = t

import pytest
from app import app as flask_app



@pytest.fixture()
def app():
    flask_app.config.update({"TESTING": True})
    ctx = flask_app.app_context()
    ctx.push()
    try:
        yield flask_app
    finally:
        ctx.pop()

@pytest.fixture()
def client(app):
    return app.test_client()
