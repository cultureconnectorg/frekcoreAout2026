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
    if (!resp.ok) {
      throw new Error(`FREKCORE Registry request failed: GET ${path} -> ${resp.status}`);
    }
    return (await resp.json()) as T;
  }

  private async postJson<T>(path: string, body: unknown): Promise<T> {
    const resp = await this.fetchImpl(`${this.baseUrl}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!resp.ok) {
      throw new Error(`FREKCORE Registry request failed: POST ${path} -> ${resp.status}`);
    }
    return (await resp.json()) as T;
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
}
