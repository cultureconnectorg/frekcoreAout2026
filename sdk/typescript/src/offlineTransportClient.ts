/**
 * OfflineTransportClient — FREKCORE TypeScript SDK (STATE_7, 2026-09-03).
 * Mirrors sdk/python/frekcore_sdk/offline_transport_client.py exactly.
 *
 * | Method       | Endpoint                                     |
 * |--------------|----------------------------------------------------|
 * | getProtocols   | GET /api/v1/offline/protocols                       |
 * | getEnvelope      | GET /api/v1/offline/envelopes/{envelopeId}            |
 *
 * See backend/offline_transport/routes.py. Envelope create/receive/sync
 * and device registration are intentionally not wrapped this state — see
 * docs/architecture/FREKCORE_SDK_CONTRACT_V1.md's own scope note.
 */

import { FetchLike } from "./registryClient";
import { raiseForFrekStatus } from "./errors";

export class OfflineTransportClient {
  private readonly baseUrl: string;
  private readonly fetchImpl: FetchLike;

  constructor(baseUrl: string, fetchImpl: FetchLike = fetch) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.fetchImpl = fetchImpl;
  }

  /** GET /api/v1/offline/protocols. Public, no auth. */
  async getProtocols(): Promise<Record<string, unknown>> {
    const path = "/api/v1/offline/protocols";
    const resp = await this.fetchImpl(`${this.baseUrl}${path}`, { method: "GET" });
    await raiseForFrekStatus(resp, path);
    return (await resp.json()) as Record<string, unknown>;
  }

  /**
   * GET /api/v1/offline/envelopes/{envelopeId}. Requires the issuing
   * holder's own session or an admin key, matching the server route.
   */
  async getEnvelope(
    envelopeId: string,
    options: { sessionToken?: string; adminKey?: string } = {}
  ): Promise<Record<string, unknown>> {
    const headers: Record<string, string> = {};
    if (options.sessionToken) headers["X-FREK-Session"] = options.sessionToken;
    if (options.adminKey) headers["X-Admin-Key"] = options.adminKey;
    const path = `/api/v1/offline/envelopes/${encodeURIComponent(envelopeId)}`;
    const resp = await this.fetchImpl(`${this.baseUrl}${path}`, { method: "GET", headers });
    await raiseForFrekStatus(resp, path);
    return (await resp.json()) as Record<string, unknown>;
  }
}
