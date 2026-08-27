import sys
import pathlib

BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app
    with TestClient(app) as c:
        yield c
