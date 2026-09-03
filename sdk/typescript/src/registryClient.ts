/**
 * FrekcoreRegistryClient — FREKCORE TypeScript SDK (Phase 2, Priority 7).
 *
 * Scope, deliberately narrow — same reasoning as sdk/python/frekcore_sdk:
 * wraps ONLY `/api/v1/registry/*`. See sdk/python/frekcore_sdk/__init__.py
 * for the full explanation of why every other FREKCORE API family is not
 * wrapped yet, and reports/12_PHASE2_IMPLEMENTATION.md.
 *
 * | Method               | Endpoint                                     |
 * |-----------------------|-----------------------------------------------|
 * | listVersions            | GET  /api/v1/registry/versions               |
 * | listNamespaces           | GET  /api/v1/registry/namespaces              |
 * | getNamespaceSchema        | GET  /api/v1/registry/namespaces/{namespace}   |
 * | validate                  | POST /api/v1/registry/validate                 |
 * | listEvents                 | GET  /api/v1/registry/events                  |
 * | createObject                | POST /api/v1/registry/objects/{namespace}      |
 * | listObjects                 | GET  /api/v1/registry/objects/{namespace}      |
 * | getObject                    | GET  /api/v1/registry/objects/{namespace}/{frekId} |
 *
 * `createObject` requires the same authority the server itself requires
 * (backend/registry/routes.py::_authorize_write): either a `bearerToken`
 * (an OAuth2 client holding the `registry:write` permission) or a
 * `sessionToken` (an identity_engine holder session, `X-FREK-Session`).
 * This client does not choose one for you; a call with neither gets the
 * same 403 the server would return.
 *
 * Uses the global `fetch` (available in Node 18+ and every browser this SDK
 * targets — no runtime HTTP dependency is introduced).
 */

export interface RegistryNamespace {
  namespace: string;
  version: string;
  title: string;
  description: string;
  schema_url: string;
}

export interface ValidationResult {
  valid: boolean;
  namespace: string;
  schema_version: string;
  errors: string[];
}

export interface RegistryVersionsResponse {
  versions: string[];
  default: string;
}

export interface EventRegistryCatalogEntry {
  event_type: string;
  version: string;
  description: string;
  producer: string;
  implemented: boolean;
  status: string;
  evidence: string;
}

export interface EventRegistryResponse {
  event_registry_version: string;
  envelope_schema: Record<string, unknown>;
  catalog: EventRegistryCatalogEntry[];
  legacy_stage_log?: Record<string, unknown>;
}

export interface RegistryObjectEnvelope {
  frek_id: string;
  entity_type: string;
  status: string;
  created_at: string;
  version: number;
  owner_id: string | null;
  [key: string]: unknown;
}

export interface RegistryObjectListResponse {
  namespace: string;
  count: number;
  total: number;
  objects: RegistryObjectEnvelope[];
}

export interface WriteAuthOptions {
  /** OAuth2 client bearer token (ISSUER authority — needs `registry:write`). */
  bearerToken?: string;
  /** identity_engine holder session token (OWNER authority). */
  sessionToken?: string;
}

export interface ListObjectsOptions {
  schemaVersion?: string;
  ownerId?: string;
  status?: string;
  limit?: number;
  offset?: number;
}

import { raiseForFrekStatus } from "./errors";

export type FetchLike = (input: string, init?: RequestInit) => Promise<Response>;

export class FrekcoreRegistryClient {
  private readonly baseUrl: string;
  private readonly fetchImpl: FetchLike;

  constructor(baseUrl: string, fetchImpl: FetchLike = fetch) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.fetchImpl = fetchImpl;
  }

  private async getJson<T>(path: string): Promise<T> {
    const resp = await this.fetchImpl(`${this.baseUrl}${path}`, { method: "GET" });
    await raiseForFrekStatus(resp, path);
    return (await resp.json()) as T;
  }

  private async postJson<T>(
    path: string,
    body: unknown,
    extraHeaders: Record<string, string> = {}
  ): Promise<T> {
    const resp = await this.fetchImpl(`${this.baseUrl}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...extraHeaders },
      body: JSON.stringify(body),
    });
    await raiseForFrekStatus(resp, path);
    return (await resp.json()) as T;
  }

  private static writeAuthHeaders(auth: WriteAuthOptions): Record<string, string> {
    const headers: Record<string, string> = {};
    if (auth.bearerToken) headers["Authorization"] = `Bearer ${auth.bearerToken}`;
    if (auth.sessionToken) headers["X-FREK-Session"] = auth.sessionToken;
    return headers;
  }

  async listVersions(): Promise<RegistryVersionsResponse> {
    return this.getJson<RegistryVersionsResponse>("/api/v1/registry/versions");
  }

  async listNamespaces(schemaVersion = "v1"): Promise<RegistryNamespace[]> {
    return this.getJson<RegistryNamespace[]>(`/api/v1/registry/namespaces?schema_version=${schemaVersion}`);
  }

  async getNamespaceSchema(namespace: string, schemaVersion = "v1"): Promise<Record<string, unknown>> {
    return this.getJson<Record<string, unknown>>(
      `/api/v1/registry/namespaces/${encodeURIComponent(namespace)}?schema_version=${schemaVersion}`
    );
  }

  async validate(
    namespace: string,
    payload: Record<string, unknown>,
    schemaVersion = "v1"
  ): Promise<ValidationResult> {
    return this.postJson<ValidationResult>("/api/v1/registry/validate", {
      namespace,
      payload,
      schema_version: schemaVersion,
    });
  }

  async listEvents(): Promise<EventRegistryResponse> {
    return this.getJson<EventRegistryResponse>("/api/v1/registry/events");
  }

  /**
   * POST /api/v1/registry/objects/{namespace}. `payload` is the
   * namespace-specific fields only — envelope fields (frek_id, entity_type,
   * status, created_at, version) are filled in server-side. See
   * `WriteAuthOptions` above for the required `auth`.
   */
  async createObject(
    namespace: string,
    payload: Record<string, unknown>,
    auth: WriteAuthOptions,
    schemaVersion = "v1"
  ): Promise<RegistryObjectEnvelope> {
    return this.postJson<RegistryObjectEnvelope>(
      `/api/v1/registry/objects/${encodeURIComponent(namespace)}`,
      { payload, schema_version: schemaVersion },
      FrekcoreRegistryClient.writeAuthHeaders(auth)
    );
  }

  /** GET /api/v1/registry/objects/{namespace}. Public, no auth required. */
  async listObjects(
    namespace: string,
    options: ListObjectsOptions = {}
  ): Promise<RegistryObjectListResponse> {
    const params = new URLSearchParams({
      schema_version: options.schemaVersion ?? "v1",
      limit: String(options.limit ?? 50),
      offset: String(options.offset ?? 0),
    });
    if (options.ownerId) params.set("owner_id", options.ownerId);
    if (options.status) params.set("status", options.status);
    return this.getJson<RegistryObjectListResponse>(
      `/api/v1/registry/objects/${encodeURIComponent(namespace)}?${params.toString()}`
    );
  }

  /** GET /api/v1/registry/objects/{namespace}/{frekId}. Public, no auth. */
  async getObject(
    namespace: string,
    frekId: string,
    schemaVersion = "v1"
  ): Promise<RegistryObjectEnvelope> {
    return this.getJson<RegistryObjectEnvelope>(
      `/api/v1/registry/objects/${encodeURIComponent(namespace)}/${encodeURIComponent(
        frekId
      )}?schema_version=${schemaVersion}`
    );
  }
}
