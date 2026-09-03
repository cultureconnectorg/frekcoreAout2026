import { strict as assert } from "node:assert";
import { test } from "node:test";
import { RelationshipGraphClient } from "../src/relationshipGraphClient";
import { FetchLike } from "../src/registryClient";

test("createRelationship posts the expected body and parses the real response shape", async () => {
  let capturedBody: unknown;
  const fetchImpl: FetchLike = async (input, init) => {
    assert.equal(new URL(input).pathname, "/api/v1/relationships");
    capturedBody = JSON.parse(init?.body as string);
    return new Response(
      JSON.stringify({ relationship_id: "r-1", subject_id: "OBJ-1", predicate: "created_by", layer: "trust" }),
      { status: 200 }
    );
  };
  const client = new RelationshipGraphClient("https://frekcore.example.com", fetchImpl);
  const result = await client.createRelationship({
    subjectId: "OBJ-1",
    predicate: "created_by",
    objectId: "ARTIST-1",
    origin: "declared",
    statement: "OBJ-1 was created by ARTIST-1",
    adminKey: "secret",
  });
  assert.equal(result.layer, "trust");
  assert.equal((capturedBody as Record<string, unknown>).subject_id, "OBJ-1");
});

test("getNeighbors builds query params and parses the real response shape", async () => {
  const fetchImpl: FetchLike = async (input) => {
    const url = new URL(input);
    assert.equal(url.pathname, "/api/v1/relationships/entity/OBJ-1/neighbors");
    assert.equal(url.searchParams.get("direction"), "both");
    return new Response(
      JSON.stringify({ entity_id: "OBJ-1", direction: "both", neighbors_count: 0, neighbors: [] }),
      { status: 200 }
    );
  };
  const client = new RelationshipGraphClient("https://frekcore.example.com", fetchImpl);
  const result = await client.getNeighbors("OBJ-1");
  assert.equal(result.neighbors_count, 0);
});
