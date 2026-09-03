import { strict as assert } from "node:assert";
import { test } from "node:test";
import { OfflineTransportClient } from "../src/offlineTransportClient";
import { FetchLike } from "../src/registryClient";
import { NotFoundError } from "../src/errors";

test("getProtocols fetches the protocol catalog with no auth", async () => {
  const fetchImpl: FetchLike = async (input) => {
    assert.equal(new URL(input).pathname, "/api/v1/offline/protocols");
    return new Response(JSON.stringify({ protocols: { bluetooth_ble: {} } }), { status: 200 });
  };
  const client = new OfflineTransportClient("https://frekcore.example.com", fetchImpl);
  const result = await client.getProtocols();
  assert.ok("bluetooth_ble" in (result.protocols as Record<string, unknown>));
});

test("getEnvelope sends the admin key header", async () => {
  let capturedHeaders: Record<string, string> | undefined;
  const fetchImpl: FetchLike = async (input, init) => {
    capturedHeaders = {};
    new Headers(init?.headers).forEach((value, key) => {
      capturedHeaders![key] = value;
    });
    assert.equal(new URL(input).pathname, "/api/v1/offline/envelopes/env-1");
    return new Response(JSON.stringify({ envelope_id: "env-1" }), { status: 200 });
  };
  const client = new OfflineTransportClient("https://frekcore.example.com", fetchImpl);
  const result = await client.getEnvelope("env-1", { adminKey: "secret" });
  assert.equal(result.envelope_id, "env-1");
  assert.equal(capturedHeaders?.["x-admin-key"], "secret");
});

test("getEnvelope unknown id raises NotFoundError", async () => {
  const fetchImpl: FetchLike = async () =>
    new Response(JSON.stringify({ detail: "envelope_introuvable" }), { status: 404 });
  const client = new OfflineTransportClient("https://frekcore.example.com", fetchImpl);
  await assert.rejects(() => client.getEnvelope("does-not-exist"), NotFoundError);
});
