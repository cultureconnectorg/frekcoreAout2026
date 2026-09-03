/**
 * CreativeLifecycleClient — FREKCORE TypeScript SDK (STATE_7, 2026-09-03).
 * Mirrors sdk/python/frekcore_sdk/creative_lifecycle_client.py exactly.
 *
 * | Method       | Endpoint                                     |
 * |--------------|---------------------------------------------------|
 * | startGenesis   | POST /api/v1/creative-lifecycle/genesis              |
 * | getHistory       | GET  /api/v1/creative-lifecycle/{preId}               |
 *
 * See backend/creative_lifecycle/routes.py. WORKSHOP/METAMORPHOSE/
 * EMISSION/LEGACY are intentionally not wrapped this state — see
 * docs/architecture/FREKCORE_SDK_CONTRACT_V1.md's own scope note.
 */

import { FetchLike } from "./registryClient";
import { raiseForFrekStatus } from "./errors";

export interface StartGenesisOptions {
  concept?: string;
  lieu?: string;
  description?: string;
  sessionToken?: string;
  adminKey?: string;
}

export class CreativeLifecycleClient {
  private readonly baseUrl: string;
  private readonly fetchImpl: FetchLike;

  constructor(baseUrl: string, fetchImpl: FetchLike = fetch) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.fetchImpl = fetchImpl;
  }

  /**
   * POST /api/v1/creative-lifecycle/genesis. Requires a holder session or
   * an admin key, same as the server route.
   */
  async startGenesis(options: StartGenesisOptions = {}): Promise<Record<string, unknown>> {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (options.sessionToken) headers["X-FREK-Session"] = options.sessionToken;
    if (options.adminKey) headers["X-Admin-Key"] = options.adminKey;
    const resp = await this.fetchImpl(`${this.baseUrl}/api/v1/creative-lifecycle/genesis`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        concept: options.concept,
        lieu: options.lieu,
        description: options.description,
      }),
    });
    await raiseForFrekStatus(resp, "/api/v1/creative-lifecycle/genesis");
    return (await resp.json()) as Record<string, unknown>;
  }

  /** GET /api/v1/creative-lifecycle/{preId}. Public, no auth. */
  async getHistory(preId: string): Promise<Record<string, unknown>> {
    const path = `/api/v1/creative-lifecycle/${encodeURIComponent(preId)}`;
    const resp = await this.fetchImpl(`${this.baseUrl}${path}`, { method: "GET" });
    await raiseForFrekStatus(resp, path);
    return (await resp.json()) as Record<string, unknown>;
  }
}
