import { strict as assert } from "node:assert";
import { test } from "node:test";
import {
  AuthenticationError,
  AuthorityError,
  ConflictError,
  FrekError,
  InternalError,
  InvalidRequestError,
  NotFoundError,
  RateLimitError,
  raiseForFrekStatus,
} from "../src/errors";

test("raiseForFrekStatus is a no-op for a 2xx response", async () => {
  const resp = new Response(JSON.stringify({ ok: true }), { status: 200 });
  await raiseForFrekStatus(resp, "/some/path");
});

const CASES: [number, new (...args: never[]) => FrekError][] = [
  [400, InvalidRequestError],
  [401, AuthenticationError],
  [403, AuthorityError],
  [404, NotFoundError],
  [409, ConflictError],
  [422, InvalidRequestError],
  [429, RateLimitError],
  [500, InternalError],
];

for (const [status, ErrorClass] of CASES) {
  test(`raiseForFrekStatus maps HTTP ${status} to ${ErrorClass.name}`, async () => {
    const resp = new Response(JSON.stringify({ detail: { code: "X", message: "boom" } }), { status });
    await assert.rejects(() => raiseForFrekStatus(resp, "/some/path"), ErrorClass);
  });
}

test("FrekError carries the original response status", async () => {
  const resp = new Response(JSON.stringify({ detail: "not found" }), { status: 404 });
  try {
    await raiseForFrekStatus(resp, "/some/path");
    assert.fail("expected raiseForFrekStatus to throw");
  } catch (err) {
    assert.ok(err instanceof NotFoundError);
    assert.equal((err as NotFoundError).status, 404);
    assert.equal((err as NotFoundError).code, "NOT_FOUND");
  }
});

test("raiseForFrekStatus falls back to a generic message for a non-JSON body", async () => {
  const resp = new Response("plain text error", { status: 500 });
  await assert.rejects(() => raiseForFrekStatus(resp, "/some/path"), InternalError);
});
