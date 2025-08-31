# tests/conftest.py
import os, sys, types
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

# --- stub torch with cuda.is_available() -> False ---
if "torch" not in sys.modules:
    torch_stub = types.ModuleType("torch")
    class _Cuda:
        @staticmethod
        def is_available(): return False
    torch_stub.cuda = _Cuda()
    sys.modules["torch"] = torch_stub

# (optional) facenet_pytorch stub if app imports it
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
