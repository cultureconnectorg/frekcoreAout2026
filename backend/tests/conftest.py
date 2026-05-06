"""
Conftest pytest — resout BASE_URL pour tous les tests backend.

Strategie :
1. Si TEST_BACKEND_URL est explicitement set (CI/CD), l'utiliser
2. Sinon utiliser http://localhost:8001 (rapide, in-cluster)
3. Forcer REACT_APP_BACKEND_URL=localhost pour les tests pour eviter timeouts via ingress
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Charge backend/.env (necessaire pour SECRET_KEY, MONGO_URL, etc.)
BACKEND_ENV = Path(__file__).resolve().parent.parent / ".env"
if BACKEND_ENV.exists():
    load_dotenv(BACKEND_ENV, override=False)

# Determine la base URL de test
TEST_BASE_URL = os.environ.get("TEST_BACKEND_URL") or "http://localhost:8001"

# Force REACT_APP_BACKEND_URL pour les tests qui le lisent
# (evite les timeouts via ingress preview qui couperait apres 15s)
os.environ["REACT_APP_BACKEND_URL"] = TEST_BASE_URL
