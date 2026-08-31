import { strict as assert } from "node:assert";
import { test } from "node:test";
import { FrekcoreIdentityClient, FetchLike } from "../src/identityClient";

/**
 * Same technique as test/registryClient.test.ts: mock `fetch`, assert
 * against real response shapes captured from the actual server (see
 * sdk/python/tests/test_identity_client.py for the equivalent suite
 * running against the real FastAPI router in-process).
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

test("getIdentity fetches the public view with no auth header", async () => {
  let capturedHeaders: Record<string, string> | undefined;
  const fetchImpl: FetchLike = async (input, init) => {
    capturedHeaders = {};
    new Headers(init?.headers).forEach((value, key) => {
      capturedHeaders![key] = value;
    });
    assert.equal(new URL(input).pathname, "/api/v1/identity/id-abcdef012345-ab12");
    return new Response(
      JSON.stringify({
        frek_id: "id-abcdef012345-ab12",
        identity_type: "individual",
        display_name: "Luciole",
        status: "active",
        created_at: "2026-08-31T00:00:00Z",
      }),
      { status: 200 }
    );
  };
  const client = new FrekcoreIdentityClient("https://frekcore.example.com", fetchImpl);
  const identity = await client.getIdentity("id-abcdef012345-ab12");
  assert.equal(identity.display_name, "Luciole");
  assert.equal(Object.keys(capturedHeaders ?? {}).length, 0);
});

test("getIdentity non-2xx response raises", async () => {
  const fetchImpl: FetchLike = async () => new Response("not found", { status: 404 });
  const client = new FrekcoreIdentityClient("https://frekcore.example.com", fetchImpl);
  await assert.rejects(() => client.getIdentity("id-doesnotexist-0000"));
});

test("getMe sends the session token header", async () => {
  let capturedHeaders: Record<string, string> | undefined;
  const fetchImpl: FetchLike = async (input, init) => {
    capturedHeaders = {};
    new Headers(init?.headers).forEach((value, key) => {
      capturedHeaders![key] = value;
    });
    assert.equal(new URL(input).pathname, "/api/v1/identity/me");
    return new Response(
      JSON.stringify({
        frek_id: "id-abcdef012345-ab12",
        identity_type: "individual",
        status: "active",
        created_at: "t",
      }),
      { status: 200 }
    );
  };
  const client = new FrekcoreIdentityClient("https://frekcore.example.com", fetchImpl);
  const me = await client.getMe("holder-session");
  assert.equal(me.frek_id, "id-abcdef012345-ab12");
  assert.equal(capturedHeaders?.["x-frek-session"], "holder-session");
});

test("getLinkedObjects sends the session token and parses the real response shape", async () => {
  const fetchImpl = fakeFetch({
    "GET /api/v1/identity/id-abcdef012345-ab12/objects": {
      status: 200,
      body: {
        frek_id: "id-abcdef012345-ab12",
        moments: [],
        fk_objects: [{ frek_id: "frek-fk-1" }],
        linked_sessions_count: 0,
      },
    },
  });
  const client = new FrekcoreIdentityClient("https://frekcore.example.com", fetchImpl);
  const result = await client.getLinkedObjects("id-abcdef012345-ab12", "holder-session");
  assert.equal(result.fk_objects.length, 1);
});

test("searchIdentities builds query params and sends the admin key header", async () => {
  let capturedHeaders: Record<string, string> | undefined;
  const fetchImpl: FetchLike = async (input, init) => {
    capturedHeaders = {};
    new Headers(init?.headers).forEach((value, key) => {
      capturedHeaders![key] = value;
    });
    assert.equal(
      `${new URL(input).pathname}${new URL(input).search}`,
      "/api/v1/identity/search?limit=50&offset=0&display_name=Luciole"
    );
    return new Response(
      JSON.stringify({
        count: 1,
        total: 1,
        identities: [
          {
            frek_id: "id-abcdef012345-ab12",
            identity_type: "individual",
            display_name: "Luciole",
            status: "active",
            created_at: "t",
          },
        ],
      }),
      { status: 200 }
    );
  };
  const client = new FrekcoreIdentityClient("https://frekcore.example.com", fetchImpl);
  const result = await client.searchIdentities("admin-key", { displayName: "Luciole" });
  assert.equal(result.total, 1);
  assert.equal(capturedHeaders?.["x-admin-key"], "admin-key");
});

test("searchIdentities without a valid admin key raises", async () => {
  const fetchImpl: FetchLike = async () => new Response("forbidden", { status: 403 });
  const client = new FrekcoreIdentityClient("https://frekcore.example.com", fetchImpl);
  await assert.rejects(() => client.searchIdentities("wrong-key"));
});
