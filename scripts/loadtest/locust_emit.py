"""
FREK Sprint F — Locust Scenario 2 : Emission (chemin critique de valeur)

Simule la creation d'un FREK-ID + toutes les etapes de generation d'artefacts.
C'est le chemin le plus couteux : ecriture Mongo + notarisation FREK-Chain + OTS submit.

Chaque VU (virtual user) :
 1. Auth token (une seule fois, cache)
 2. POST identity/emit  -> creation FREK-ID + block notarise
 3. GET  passport/{id}  -> generation signature Ed25519
 4. GET  did/{id}       -> generation DID Document
 5. GET  vc/{id}        -> generation VC eddsa-jcs-2022

On mesure le chemin bout-en-bout d'un "porteur qui recoit son identite".
"""
import os
import time
import uuid
from locust import HttpUser, task, between, events

API = os.environ.get("FREK_API", "http://localhost:8001")
CID = os.environ.get("FREK_CID", "kiltikonet-cc2026")
CSEC = os.environ.get("FREK_CSEC", "")


class EmitUser(HttpUser):
    wait_time = between(0.5, 2.0)
    host = API
    token = None

    def on_start(self):
        r = self.client.post(
            "/api/v1/auth/token",
            json={"client_id": CID, "client_secret": CSEC, "grant_type": "client_credentials"},
            name="[bootstrap] /auth/token",
        )
        if r.ok:
            self.token = r.json().get("access_token")
        self.frek_id_cache = None

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(3)
    def full_emission_pipeline(self):
        """Chemin critique de valeur : creation -> passport -> DID -> VC."""
        if not self.token:
            return
        # Unique email per virtual user + timestamp for uniqueness
        email = f"perf-{uuid.uuid4().hex[:12]}-{int(time.time()*1000)}@frek.perf"

        t0 = time.time()
        r = self.client.post(
            "/api/v1/identity/emit",
            headers=self._headers(),
            json={"email": email, "source": "perf_test", "event": "PERF_F"},
            name="[emit] identity/emit",
        )
        if not r.ok:
            return
        frek_id = r.json().get("frek_id")
        self.frek_id_cache = frek_id
        t_emit = time.time() - t0

        # Immediately fetch derivatives
        self.client.get(f"/api/v1/passport/{frek_id}", name="[emit] passport/[id]")
        self.client.get(f"/api/v1/did/{frek_id}", name="[emit] did/[id]")
        self.client.get(f"/api/v1/vc/{frek_id}", name="[emit] vc/[id]")

        # Custom metric : record end-to-end emission latency
        events.request.fire(
            request_type="EMIT_PIPELINE",
            name="[pipeline] full_emission_e2e",
            response_time=int((time.time() - t0) * 1000),
            response_length=0,
            exception=None,
            context={},
        )

    @task(1)
    def status_check(self):
        if self.frek_id_cache:
            self.client.get(f"/api/v1/identity/{self.frek_id_cache}/status",
                            name="[emit] identity/[id]/status")
