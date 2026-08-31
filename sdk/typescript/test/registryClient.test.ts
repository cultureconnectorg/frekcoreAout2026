import { strict as assert } from "node:assert";
import { test } from "node:test";
import { FrekcoreRegistryClient, FetchLike } from "../src/registryClient";

/**
 * These tests mock `fetch` — this sandbox has no live FREKCORE server to hit
 * (see reports/09_PHASE2_BASELINE.md), and no ASGI-transport equivalent for
 * a TypeScript HTTP client. They verify request construction (method, path,
 * body) and response parsing are correct against the *real* JSON shapes the
 * server returns (copied from an actual `GET /api/v1/registry/namespaces`
 * response body captured via sdk/python/tests/test_registry_client.py,
 * kept in sync by hand — see reports/13_PHASE2_GAP_ANALYSIS.md for this
 * being a named gap: no automated cross-language contract test exists yet).
 */

function fakeFetch(responses: Record<string, { status: number; body: unknown }>): FetchLike {
  return async (input: string, init?: RequestInit) => {
    const key = `${init?.method ?? "GET"} ${new URL(input).pathname}${new URL(input).search}`;
    const match = responses[key];
    if (!match) {
      throw new Error(`unexpected request: ${key}`);
    }
    return new Response(JSON.stringify(match.body), { status: match.status });
  };
}

test("listNamespaces parses the real response shape", async () => {
  const fetchImpl = fakeFetch({
    "GET /api/v1/registry/namespaces?schema_version=v1": {
      status: 200,
      body: [
        {
          namespace: "frek.artist",
          version: "1.0.0",
          title: "FREK Artist",
          description: "...",
          schema_url: "/api/v1/registry/namespaces/frek.artist?schema_version=v1",
        },
      ],
    },
  });
  const client = new FrekcoreRegistryClient("https://frekcore.example.com", fetchImpl);
  const namespaces = await client.listNamespaces();
  assert.equal(namespaces.length, 1);
  assert.equal(namespaces[0].namespace, "frek.artist");
});

test("validate posts the expected body and parses errors", async () => {
  const fetchImpl = fakeFetch({
    "POST /api/v1/registry/validate": {
      status: 200,
      body: {
        valid: false,
        namespace: "frek.artist",
        schema_version: "v1",
        errors: ["<root>: 'display_name' is a required property"],
      },
    },
  });
  const client = new FrekcoreRegistryClient("https://frekcore.example.com", fetchImpl);
  const result = await client.validate("frek.artist", { entity_type: "frek.artist" });
  assert.equal(result.valid, false);
  assert.equal(result.errors.length, 1);
});

test("non-2xx response raises", async () => {
  const fetchImpl: FetchLike = async () => new Response("not found", { status: 404 });
  const client = new FrekcoreRegistryClient("https://frekcore.example.com", fetchImpl);
  await assert.rejects(() => client.getNamespaceSchema("frek.nope"));
});

test("createObject sends the bearer token and parses the real envelope shape", async () => {
  let capturedHeaders: Record<string, string> | undefined;
  const fetchImpl: FetchLike = async (input, init) => {
    capturedHeaders = {};
    new Headers(init?.headers).forEach((value, key) => {
      capturedHeaders![key] = value;
    });
    assert.equal(new URL(input).pathname, "/api/v1/registry/objects/frek.artist");
    assert.deepEqual(JSON.parse(init!.body as string), {
      payload: { display_name: "Test Artist" },
      schema_version: "v1",
    });
    return new Response(
      JSON.stringify({
        frek_id: "frek-abcdef012345-0001",
        entity_type: "frek.artist",
        status: "draft",
        created_at: "2026-08-31T00:00:00Z",
        version: 1,
        owner_id: null,
        display_name: "Test Artist",
      }),
      { status: 201 }
    );
  };
  const client = new FrekcoreRegistryClient("https://frekcore.example.com", fetchImpl);
  const obj = await client.createObject(
    "frek.artist",
    { display_name: "Test Artist" },
    { bearerToken: "issuer-token" }
  );
  assert.equal(obj.frek_id, "frek-abcdef012345-0001");
  assert.equal(capturedHeaders?.["authorization"], "Bearer issuer-token");
  assert.equal(capturedHeaders?.["x-frek-session"], undefined);
});

test("createObject sends the session token when used instead", async () => {
  let capturedHeaders: Record<string, string> | undefined;
  const fetchImpl: FetchLike = async (_input, init) => {
    capturedHeaders = {};
    new Headers(init?.headers).forEach((value, key) => {
      capturedHeaders![key] = value;
    });
    return new Response(JSON.stringify({ frek_id: "id-x", entity_type: "frek.artist", status: "draft", created_at: "t", version: 1, owner_id: "id-x" }), { status: 201 });
  };
  const client = new FrekcoreRegistryClient("https://frekcore.example.com", fetchImpl);
  await client.createObject("frek.artist", { display_name: "X" }, { sessionToken: "holder-session" });
  assert.equal(capturedHeaders?.["x-frek-session"], "holder-session");
  assert.equal(capturedHeaders?.["authorization"], undefined);
});

test("listObjects builds query params and parses the real list shape", async () => {
  const fetchImpl = fakeFetch({
    "GET /api/v1/registry/objects/frek.artist?schema_version=v1&limit=50&offset=0&owner_id=id-x&status=draft": {
      status: 200,
      body: {
        namespace: "frek.artist",
        count: 1,
        total: 1,
        objects: [
          {
            frek_id: "frek-abcdef012345-0001",
            entity_type: "frek.artist",
            status: "draft",
            created_at: "2026-08-31T00:00:00Z",
            version: 1,
            owner_id: "id-x",
            display_name: "Test Artist",
          },
        ],
      },
    },
  });
  const client = new FrekcoreRegistryClient("https://frekcore.example.com", fetchImpl);
  const result = await client.listObjects("frek.artist", { ownerId: "id-x", status: "draft" });
  assert.equal(result.count, 1);
  assert.equal(result.objects[0].frek_id, "frek-abcdef012345-0001");
});

test("getObject fetches a single object by frek_id", async () => {
  const fetchImpl = fakeFetch({
    "GET /api/v1/registry/objects/frek.artist/frek-abcdef012345-0001?schema_version=v1": {
      status: 200,
      body: {
        frek_id: "frek-abcdef012345-0001",
        entity_type: "frek.artist",
        status: "draft",
        created_at: "2026-08-31T00:00:00Z",
        version: 1,
        owner_id: null,
        display_name: "Test Artist",
      },
    },
  });
  const client = new FrekcoreRegistryClient("https://frekcore.example.com", fetchImpl);
  const obj = await client.getObject("frek.artist", "frek-abcdef012345-0001");
  assert.equal(obj.display_name, "Test Artist");
});
