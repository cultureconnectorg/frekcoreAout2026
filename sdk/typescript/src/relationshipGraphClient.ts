/**
 * RelationshipGraphClient — FREKCORE TypeScript SDK (STATE_7, 2026-09-03).
 * Mirrors sdk/python/frekcore_sdk/relationship_graph_client.py exactly.
 *
 * | Method             | Endpoint                                        |
 * |---------------------|-----------------------------------------------------|
 * | createRelationship    | POST /api/v1/relationships                             |
 * | getNeighbors            | GET  /api/v1/relationships/entity/{entityId}/neighbors   |
 *
 * See backend/relationship_graph/routes.py. verify/revoke and the
 * traverse/path + {id}/history reads are intentionally not wrapped this
 * state — see docs/architecture/FREKCORE_SDK_CONTRACT_V1.md's own scope
 * note.
 */

import { FetchLike } from "./registryClient";
import { raiseForFrekStatus } from "./errors";

export interface CreateRelationshipOptions {
  subjectId: string;
  predicate: string;
  objectId: string;
  origin: string;
  statement: string;
  subjectType?: string;
  objectType?: string;
  data?: Record<string, unknown>;
  sessionToken?: string;
  adminKey?: string;
}

export interface NeighborsResponse {
  entity_id: string;
  direction: string;
  neighbors_count: number;
  neighbors: Record<string, unknown>[];
}

export class RelationshipGraphClient {
  private readonly baseUrl: string;
  private readonly fetchImpl: FetchLike;

  constructor(baseUrl: string, fetchImpl: FetchLike = fetch) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.fetchImpl = fetchImpl;
  }

  /**
   * POST /api/v1/relationships. `origin` is one of the D6 ClaimOrigin
   * values ("declared", "observed", "attested", "computed", "inferred")
   * -- a holder session may only self-assert "declared"; other origins
   * require an admin key, matching the server route's own authority
   * split.
   */
  async createRelationship(options: CreateRelationshipOptions): Promise<Record<string, unknown>> {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (options.sessionToken) headers["X-FREK-Session"] = options.sessionToken;
    if (options.adminKey) headers["X-Admin-Key"] = options.adminKey;
    const resp = await this.fetchImpl(`${this.baseUrl}/api/v1/relationships`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        subject_id: options.subjectId,
        subject_type: options.subjectType,
        predicate: options.predicate,
        object_id: options.objectId,
        object_type: options.objectType,
        origin: options.origin,
        statement: options.statement,
        data: options.data ?? {},
      }),
    });
    await raiseForFrekStatus(resp, "/api/v1/relationships");
    return (await resp.json()) as Record<string, unknown>;
  }

  /**
   * GET /api/v1/relationships/entity/{entityId}/neighbors. Optionally
   * authenticated -- an unauthenticated call sees only GLOBAL-visibility
   * relationships, matching the server route's own per-section Scope
   * redaction.
   */
  async getNeighbors(
    entityId: string,
    options: { direction?: string; limit?: number } = {}
  ): Promise<NeighborsResponse> {
    const params = new URLSearchParams({
      direction: options.direction ?? "both",
      limit: String(options.limit ?? 200),
    });
    const path = `/api/v1/relationships/entity/${encodeURIComponent(entityId)}/neighbors?${params.toString()}`;
    const resp = await this.fetchImpl(`${this.baseUrl}${path}`, { method: "GET" });
    await raiseForFrekStatus(resp, path);
    return (await resp.json()) as NeighborsResponse;
  }
}
