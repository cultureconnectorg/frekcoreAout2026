"""
FREK Sprint F — Locust Scenario 1 : Lecture massive

Simule des utilisateurs qui consultent frequemment :
- pulse ecosysteme
- profil FREK-ID
- passport verify
- explorer blocks
- notary chain status
- verify page (chemin critique produit)

Poids relatif base sur un usage realiste (lecture 90% du trafic).
"""
import os
import random
from locust import HttpUser, task, between

API = os.environ.get("FREK_API", "http://localhost:8001")
# Optional : FREK-IDs precharges pour eviter cascade d'erreurs 404
KNOWN_FREK_IDS = os.environ.get("FREK_IDS", "").split(",")


class ReadUser(HttpUser):
    wait_time = between(1, 3)  # user pause 1-3s entre requetes
    host = API

    def on_start(self):
        # Precharge une liste de FREK-IDs disponibles depuis le pulse
        if not KNOWN_FREK_IDS or KNOWN_FREK_IDS == [""]:
            try:
                r = self.client.get("/api/v1/notary/blocks?limit=20", name="[bootstrap] blocks")
                blocks = r.json() if r.ok else []
                self.frek_ids = list({
                    b.get("payload_id") for b in blocks
                    if b.get("payload_type") == "identity_emit" and b.get("payload_id")
                }) or ["b6b3d5a2-2a87-4c3a-8276-30dc19d3623d"]
            except Exception:
                self.frek_ids = ["b6b3d5a2-2a87-4c3a-8276-30dc19d3623d"]
        else:
            self.frek_ids = KNOWN_FREK_IDS

    @task(20)
    def pulse(self):
        self.client.get("/api/core/ecosystem/pulse", name="/pulse")

    @task(15)
    def blocks_list(self):
        self.client.get("/api/v1/notary/blocks?limit=10", name="/notary/blocks")

    @task(10)
    def chain_status(self):
        self.client.get("/api/v1/notary/chain/status", name="/notary/chain/status")

    @task(15)
    def frek_v1_detail(self):
        fid = random.choice(self.frek_ids)
        # v1 identity/status = endpoint public le plus consulte (chemin verify)
        self.client.get(f"/api/v1/identity/{fid}/status", name="/identity/[id]/status")

    @task(10)
    def frek_stages(self):
        fid = random.choice(self.frek_ids)
        self.client.get(f"/api/v1/identity/{fid}/detail",
                        name="/identity/[id]/detail",
                        catch_response=True) if False else None
        # Skipping — detail requires auth. Public version:
        self.client.get(f"/api/v1/audit/{fid}", name="/audit/[id]", catch_response=True)

    @task(8)
    def passport_pub_key(self):
        self.client.get("/api/v1/passport/key", name="/passport/key")

    @task(7)
    def passport_get(self):
        fid = random.choice(self.frek_ids)
        self.client.get(f"/api/v1/passport/{fid}", name="/passport/[id]")

    @task(5)
    def event_stats(self):
        self.client.get("/api/core/event/CC2026/stats", name="/core/event/CC2026/stats")

    @task(3)
    def spec(self):
        self.client.get("/api/v1/spec/", name="/spec")

    @task(2)
    def wellknown_jwks(self):
        self.client.get("/api/.well-known/jwks.json", name="/.well-known/jwks.json")
