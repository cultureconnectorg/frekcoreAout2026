/**
 * FrekcoreIdentityClient — FREKCORE TypeScript SDK (Phase 2/3, Priority 7).
 *
 * Scope, deliberately narrow — mirrors sdk/python/frekcore_sdk/identity_client.py
 * exactly: wraps ONLY identity_engine's public-READ surface
 * (`/api/v1/identity/*`). The write/lifecycle surface (init, register/*,
 * authenticate/*, revocation, update, archive, link-object) is intentionally
 * not wrapped — those either need a browser/authenticator WebAuthn context
 * this SDK has no access to, or (merge/renew/recovery) have semantics still
 * pending a founder decision (docs/decisions/0002-identity-lifecycle-
 * founder-decisions-needed.md).
 *
 * | Method              | Endpoint                              | Auth                     |
 * |----------------------|------------------------------------------|----------------------------|
 * | getIdentity            | GET /api/v1/identity/{frekId}              | none (public view)          |
 * | getMe                    | GET /api/v1/identity/me                     | X-FREK-Session (required)    |
 * | getLinkedObjects           | GET /api/v1/identity/{frekId}/objects        | X-FREK-Session (required)     |
 * | searchIdentities             | GET /api/v1/identity/search                    | X-Admin-Key (required)          |
 *
 * See backend/identity_engine/routes.py for the server-side implementation
 * of each of these calls. `getIdentity` and `searchIdentities` never return
 * credentials or other sensitive fields — see that module's `_to_public()`.
 *
 * Uses the global `fetch` (available in Node 18+ and every browser this SDK
 * targets — no runtime HTTP dependency is introduced), same as
 * FrekcoreRegistryClient.
 */

import { FetchLike } from "./registryClient";
export type { FetchLike };

export interface IdentityPublicView {
  frek_id: string;
  identity_type: string;
  display_name?: string | null;
  status: string;
  created_at: string;
  [key: string]: unknown;
}

export interface SearchIdentitiesOptions {
  displayName?: string;
  status?: string;
  identityType?: string;
  limit?: number;
  offset?: number;
}

export interface SearchIdentitiesResponse {
  count: number;
  total: number;
  identities: IdentityPublicView[];
}

export interface LinkedObjectsResponse {
  frek_id: string;
  moments: Record<string, unknown>[];
  fk_objects: Record<string, unknown>[];
  linked_sessions_count: number;
}

export class FrekcoreIdentityClient {
  private readonly baseUrl: string;
  private readonly fetchImpl: FetchLike;

  constructor(baseUrl: string, fetchImpl: FetchLike = fetch) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.fetchImpl = fetchImpl;
  }

  private async getJson<T>(path: string, extraHeaders: Record<string, string> = {}): Promise<T> {
    const resp = await this.fetchImpl(`${this.baseUrl}${path}`, {
      method: "GET",
      headers: extraHeaders,
    });
    if (!resp.ok) {
      throw new Error(`FREKCORE Identity request failed: GET ${path} -> ${resp.status}`);
    }
    return (await resp.json()) as T;
  }

  /** GET /api/v1/identity/{frekId}. Public, no auth required. */
  async getIdentity(frekId: string): Promise<IdentityPublicView> {
    return this.getJson<IdentityPublicView>(`/api/v1/identity/${encodeURIComponent(frekId)}`);
  }

  /** GET /api/v1/identity/me. Requires a valid holder session token. */
  async getMe(sessionToken: string): Promise<IdentityPublicView> {
    return this.getJson<IdentityPublicView>("/api/v1/identity/me", {
      "X-FREK-Session": sessionToken,
    });
  }

  /**
   * GET /api/v1/identity/{frekId}/objects. Requires a holder session valid
   * for THIS frekId specifically — the server rejects a session that
   * verifies to a different identity.
   */
  async getLinkedObjects(frekId: string, sessionToken: string): Promise<LinkedObjectsResponse> {
    return this.getJson<LinkedObjectsResponse>(
      `/api/v1/identity/${encodeURIComponent(frekId)}/objects`,
      { "X-FREK-Session": sessionToken }
    );
  }

  /**
   * GET /api/v1/identity/search. Admin-key only, no holder path — matches
   * the server route's own design (a bulk-listing/enumeration surface has
   * no per-holder analog).
   */
  async searchIdentities(
    adminKey: string,
    options: SearchIdentitiesOptions = {}
  ): Promise<SearchIdentitiesResponse> {
    const params = new URLSearchParams({
      limit: String(options.limit ?? 50),
      offset: String(options.offset ?? 0),
    });
    if (options.displayName) params.set("display_name", options.displayName);
    if (options.status) params.set("status", options.status);
    if (options.identityType) params.set("identity_type", options.identityType);
    return this.getJson<SearchIdentitiesResponse>(`/api/v1/identity/search?${params.toString()}`, {
      "X-Admin-Key": adminKey,
    });
  }
}
