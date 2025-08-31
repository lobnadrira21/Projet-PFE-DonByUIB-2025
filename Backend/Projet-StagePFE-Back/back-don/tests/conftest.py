# tests/conftest.py
import os, sys, types
os.environ["UNIT_TEST"] = "1"   # must be before importing app

if "transformers" not in sys.modules:
    t = types.ModuleType("transformers")
    class _Dummy: pass
    t.CLIPProcessor = _Dummy
    t.CLIPModel = _Dummy
    sys.modules["transformers"] = t

# NEW: stub torch so 'import torch' at module top doesn't fail
if "torch" not in sys.modules:
    sys.modules["torch"] = types.ModuleType("torch")

# (Optional) stub facenet_pytorch too if it appears later
if "facenet_pytorch" not in sys.modules:
    f = types.ModuleType("facenet_pytorch")
    class _M: pass
    class _R: pass
    f.MTCNN = _M
    f.InceptionResnetV1 = _R
    sys.modules["facenet_pytorch"] = f

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
