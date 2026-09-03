import { strict as assert } from "node:assert";
import { test } from "node:test";
import { ContentBindingClient } from "../src/contentBindingClient";
import { FetchLike } from "../src/registryClient";
import { NotFoundError } from "../src/errors";

test("getBinding fetches a single binding with no auth", async () => {
  const fetchImpl: FetchLike = async (input) => {
    assert.equal(new URL(input).pathname, "/api/v1/content-binding/binding/b-1");
    return new Response(JSON.stringify({ binding_id: "b-1", frek_id: "fk-1" }), { status: 200 });
  };
  const client = new ContentBindingClient("https://frekcore.example.com", fetchImpl);
  const binding = await client.getBinding("b-1");
  assert.equal(binding.binding_id, "b-1");
});

test("getBinding unknown id raises NotFoundError", async () => {
  const fetchImpl: FetchLike = async () =>
    new Response(JSON.stringify({ detail: { code: "NOT_FOUND", message: "gone" } }), { status: 404 });
  const client = new ContentBindingClient("https://frekcore.example.com", fetchImpl);
  await assert.rejects(() => client.getBinding("does-not-exist"), NotFoundError);
});

test("listBindings fetches the object's binding list", async () => {
  const fetchImpl: FetchLike = async (input) => {
    assert.equal(new URL(input).pathname, "/api/v1/content-binding/fk-1");
    return new Response(JSON.stringify({ frek_id: "fk-1", count: 2, bindings: [] }), { status: 200 });
  };
  const client = new ContentBindingClient("https://frekcore.example.com", fetchImpl);
  const result = await client.listBindings("fk-1");
  assert.equal(result.count, 2);
});
