"""
FREK Sprint F — Locust Scenario 3 : Terrain simule

Simule des scanners staff qui envoient des scans d'acces sur J-0.
Chaque scanner :
 - Se logue avec un PIN une seule fois
 - Envoie ensuite N scans/minute
 - Chaque scan est idempotent (client_uuid)
 - En parallele, quelques counters universels (streams, ingest kiltikonet)

C'est le scenario le plus proche de la charge reelle CC2026 :
100 tablettes/pistolets scannent 40 000 badges sur 6h d'evenement.
"""
import os
import time
import uuid
import random
from locust import HttpUser, task, between

API = os.environ.get("FREK_API", "http://localhost:8001")
AGENT_ID = os.environ.get("FREK_STAFF_AGENT", "SUPERVISEUR-01")
AGENT_PIN = os.environ.get("FREK_STAFF_PIN", "9999")

# Pool de badges factices — le backend acceptera meme les inconnus (scan tolerant)
FAKE_BADGES = [f"BNV-2026-{i:05d}" for i in range(1, 1001)]


class FieldScanner(HttpUser):
    wait_time = between(0.3, 1.5)  # scanner envoie un scan toutes les 0.3-1.5s
    host = API
    token = None

    def on_start(self):
        r = self.client.post(
            "/api/v1/staff/login",
            json={"agent_id": AGENT_ID, "pin": AGENT_PIN},
            name="[bootstrap] /staff/login",
        )
        if r.ok:
            self.token = r.json().get("access_token")

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(20)
    def scan_access(self):
        """Scan terrain : entree/scene/exposants."""
        if not self.token:
            return
        badge = random.choice(FAKE_BADGES)
        zone = random.choice(["ENTREE", "SCENE", "EXPOSANTS"])
        self.client.post(
            "/api/v1/staff/scan/access",
            headers=self._headers(),
            json={
                "code": badge,
                "zone": zone,
                "client_uuid": str(uuid.uuid4()),
            },
            name="[field] staff/scan/access",
        )

    @task(5)
    def counter_ingest(self):
        """Compteur universel — batch souverain (kiltikonet/fms/kora)."""
        # Le counter attend un batch d'entries, source = kiltikonet, ref unique
        self.client.post(
            "/api/core/count",
            json={
                "entries": [
                    {
                        "external_ref": str(uuid.uuid4()),
                        "action": random.choice(["presence", "stream_play", "vote"]),
                        "context": "CC2026",
                        "source": "kiltikonet",
                        "idempotency_key": str(uuid.uuid4()),
                    }
                ]
            },
            name="[field] core/count",
        )

    @task(2)
    def live_stats(self):
        """Un op ouvre son dashboard en direct."""
        self.client.get("/api/v1/dashboard/cc2026/live", name="[field] dashboard/live")
