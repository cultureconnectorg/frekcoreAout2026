/**
 * ContentBindingClient — FREKCORE TypeScript SDK (STATE_7, 2026-09-03).
 * Mirrors sdk/python/frekcore_sdk/content_binding_client.py exactly.
 *
 * | Method       | Endpoint                                            |
 * |--------------|--------------------------------------------------------|
 * | getBinding     | GET /api/v1/content-binding/binding/{bindingId}          |
 * | listBindings    | GET /api/v1/content-binding/{frekId}                       |
 *
 * See backend/content_binding/routes.py. The multipart create endpoint is
 * intentionally not wrapped this state — see
 * docs/architecture/FREKCORE_SDK_CONTRACT_V1.md's own scope note.
 */

import { FetchLike } from "./registryClient";
import { raiseForFrekStatus } from "./errors";

export interface ContentBindingListResponse {
  frek_id: string;
  count: number;
  bindings: Record<string, unknown>[];
}

export class ContentBindingClient {
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

  /** GET /api/v1/content-binding/binding/{bindingId}. Public, no auth. */
  async getBinding(bindingId: string): Promise<Record<string, unknown>> {
    return this.getJson(`/api/v1/content-binding/binding/${encodeURIComponent(bindingId)}`);
  }

  /** GET /api/v1/content-binding/{frekId}. Public, no auth. */
  async listBindings(frekId: string): Promise<ContentBindingListResponse> {
    return this.getJson(`/api/v1/content-binding/${encodeURIComponent(frekId)}`);
  }
}
