/**
 * TechnicalEvidenceReportClient — FREKCORE TypeScript SDK (STATE_7,
 * 2026-09-03). Mirrors
 * sdk/python/frekcore_sdk/technical_evidence_report_client.py exactly.
 *
 * | Method          | Endpoint                                                |
 * |------------------|--------------------------------------------------------------|
 * | generateReport     | POST /api/v1/reports/technical-evidence                        |
 * | verifyReport         | GET  /api/v1/reports/technical-evidence/{reportId}/verify         |
 *
 * See backend/technical_evidence_report/routes.py. The authenticated,
 * per-section-redacted GET .../{reportId} is intentionally not wrapped
 * this state — see docs/architecture/FREKCORE_SDK_CONTRACT_V1.md's own
 * scope note; verifyReport (public) already covers the common "did this
 * report really come from FREKCORE, unmodified" integration need.
 */

import { FetchLike } from "./registryClient";
import { raiseForFrekStatus } from "./errors";

export interface GenerateReportOptions {
  subjectType: string;
  subjectId: string;
  sessionToken?: string;
  adminKey?: string;
}

export interface VerifyReportResponse {
  report_id: string;
  report_hash: string;
  integrity_verified: boolean;
  sections_summary: { kind: string; title: string }[];
  legal_disclaimer: string;
  [key: string]: unknown;
}

export class TechnicalEvidenceReportClient {
  private readonly baseUrl: string;
  private readonly fetchImpl: FetchLike;

  constructor(baseUrl: string, fetchImpl: FetchLike = fetch) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.fetchImpl = fetchImpl;
  }

  /**
   * POST /api/v1/reports/technical-evidence. `subjectType` is one of the
   * D5 ReportSubjectType values -- resolved from `subjectId` alone
   * server-side, never from any other caller-supplied fact (this client
   * only ever sends these two fields).
   */
  async generateReport(options: GenerateReportOptions): Promise<Record<string, unknown>> {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (options.sessionToken) headers["X-FREK-Session"] = options.sessionToken;
    if (options.adminKey) headers["X-Admin-Key"] = options.adminKey;
    const path = "/api/v1/reports/technical-evidence";
    const resp = await this.fetchImpl(`${this.baseUrl}${path}`, {
      method: "POST",
      headers,
      body: JSON.stringify({ subject_type: options.subjectType, subject_id: options.subjectId }),
    });
    await raiseForFrekStatus(resp, path);
    return (await resp.json()) as Record<string, unknown>;
  }

  /**
   * GET /api/v1/reports/technical-evidence/{reportId}/verify. Public, no
   * auth -- shape-only response, never section content.
   */
  async verifyReport(reportId: string): Promise<VerifyReportResponse> {
    const path = `/api/v1/reports/technical-evidence/${encodeURIComponent(reportId)}/verify`;
    const resp = await this.fetchImpl(`${this.baseUrl}${path}`, { method: "GET" });
    await raiseForFrekStatus(resp, path);
    return (await resp.json()) as VerifyReportResponse;
  }
}
