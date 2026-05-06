"""
Conftest pytest pour la suite FREK backend.

Strategie :
- Tests appellent le backend reel (uvicorn supervisor) via http://localhost:8001
  pour eviter les timeouts du proxy ingress externe.
- Au demarrage de la session (et avant chaque test) on purge la collection
  `rate_limits` pour eviter les faux positifs lies aux runs precedents.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import pytest

# Charge backend/.env (necessaire pour SECRET_KEY, MONGO_URL, etc.)
BACKEND_ENV = Path(__file__).resolve().parent.parent / ".env"
if BACKEND_ENV.exists():
    load_dotenv(BACKEND_ENV, override=False)

# URL de test : localhost en interne (rapide, pas de proxy)
TEST_BASE_URL = os.environ.get("TEST_BACKEND_URL") or "http://localhost:8001"
os.environ["REACT_APP_BACKEND_URL"] = TEST_BASE_URL


def _purge_rate_limits():
    try:
        from pymongo import MongoClient
        mongo_url = os.environ.get("MONGO_URL")
        db_name = os.environ.get("DB_NAME")
        if not mongo_url or not db_name:
            return
        mc = MongoClient(mongo_url, serverSelectionTimeoutMS=2000)
        # purge generic counters (test_security_hardening installe son propre quota)
        mc[db_name].rate_limits.delete_many({"scope": {"$nin": []}})
        mc.close()
    except Exception:
        pass


@pytest.fixture(scope="session", autouse=True)
def _session_setup():
    _purge_rate_limits()
    yield


@pytest.fixture(autouse=True)
def _per_test_purge(request):
    """Avant chaque test (sauf TestRateLimit qui pre-remplit ses quotas), purge."""
    test_class = request.node.cls.__name__ if request.node.cls else ""
    if test_class != "TestRateLimit":
        _purge_rate_limits()
    yield
