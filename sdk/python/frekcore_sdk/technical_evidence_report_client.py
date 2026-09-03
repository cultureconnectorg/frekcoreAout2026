"""FrekcoreTechnicalEvidenceReportClient — D5's generate + public-verify
surface (`/api/v1/reports/*`).

| Method          | Endpoint                                                   |
|------------------|----------------------------------------------------------------|
| generate_report   | POST /api/v1/reports/technical-evidence                          |
| verify_report      | GET  /api/v1/reports/technical-evidence/{report_id}/verify          |

See `backend/technical_evidence_report/routes.py`. `GET .../{report_id}`
(authenticated, per-section-redacted retrieval) is intentionally not
wrapped this state — see `FREKCORE_SDK_CONTRACT_V1.md`'s own scope note;
`verify_report` (public) already covers the common "did this report
really come from FREKCORE, unmodified" integration need.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from .errors import raise_for_frek_status


class FrekcoreTechnicalEvidenceReportClient:
    def __init__(
        self, base_url: Optional[str] = None, *, client: Optional[httpx.Client] = None
    ) -> None:
        if client is not None:
            self._client = client
            self._owns_client = False
        else:
            if not base_url:
                raise ValueError("base_url is required when no client is provided")
            self._client = httpx.Client(base_url=base_url.rstrip("/"))
            self._owns_client = True

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "FrekcoreTechnicalEvidenceReportClient":
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.close()

    def generate_report(
        self,
        *,
        subject_type: str,
        subject_id: str,
        session_token: Optional[str] = None,
        admin_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """POST /api/v1/reports/technical-evidence. `subject_type` is
        one of the D5 `ReportSubjectType` values (e.g. "frek_object",
        "content_binding", "relationship_record", ...) -- resolved from
        `subject_id` alone server-side, never from any other caller-
        supplied fact (ARBITRARY_CALLER_SUPPLIED_FACTS_AS_CANONICAL_TRUTH
        =FALSE, this client only ever sends these two fields)."""
        headers: Dict[str, str] = {}
        if session_token:
            headers["X-FREK-Session"] = session_token
        if admin_key:
            headers["X-Admin-Key"] = admin_key
        resp = self._client.post(
            "/api/v1/reports/technical-evidence",
            json={"subject_type": subject_type, "subject_id": subject_id},
            headers=headers,
        )
        raise_for_frek_status(resp)
        return resp.json()

    def verify_report(self, report_id: str) -> Dict[str, Any]:
        """GET /api/v1/reports/technical-evidence/{report_id}/verify.
        Public, no auth -- shape-only response, never section content
        (VERIFICATION_MAY_BE_PUBLIC=TRUE, DISCLOSURE_IS_AUTHORIZATION_
        SCOPED=TRUE)."""
        resp = self._client.get(
            f"/api/v1/reports/technical-evidence/{report_id}/verify"
        )
        raise_for_frek_status(resp)
        return resp.json()
