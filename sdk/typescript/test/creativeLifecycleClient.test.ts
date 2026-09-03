import { strict as assert } from "node:assert";
import { test } from "node:test";
import { CreativeLifecycleClient } from "../src/creativeLifecycleClient";
import { FetchLike } from "../src/registryClient";
import { AuthorityError } from "../src/errors";

test("startGenesis sends the admin key header and parses the real response shape", async () => {
  let capturedHeaders: Record<string, string> | undefined;
  const fetchImpl: FetchLike = async (input, init) => {
    capturedHeaders = {};
    new Headers(init?.headers).forEach((value, key) => {
      capturedHeaders![key] = value;
    });
    assert.equal(new URL(input).pathname, "/api/v1/creative-lifecycle/genesis");
    return new Response(JSON.stringify({ pre_id: "PRE-1", stage: "GENESIS" }), { status: 200 });
  };
  const client = new CreativeLifecycleClient("https://frekcore.example.com", fetchImpl);
  const result = await client.startGenesis({ concept: "a song", adminKey: "secret" });
  assert.equal(result.stage, "GENESIS");
  assert.equal(capturedHeaders?.["x-admin-key"], "secret");
});

test("startGenesis without any credential raises AuthorityError", async () => {
  const fetchImpl: FetchLike = async () =>
    new Response(JSON.stringify({ detail: "invalid_admin_key" }), { status: 403 });
  const client = new CreativeLifecycleClient("https://frekcore.example.com", fetchImpl);
  await assert.rejects(() => client.startGenesis({}), AuthorityError);
});

test("getHistory fetches lifecycle history with no auth", async () => {
  const fetchImpl: FetchLike = async (input) => {
    assert.equal(new URL(input).pathname, "/api/v1/creative-lifecycle/PRE-1");
    return new Response(JSON.stringify({ pre_id: "PRE-1", current_stage: "GENESIS" }), { status: 200 });
  };
  const client = new CreativeLifecycleClient("https://frekcore.example.com", fetchImpl);
  const result = await client.getHistory("PRE-1");
  assert.equal(result.current_stage, "GENESIS");
});
