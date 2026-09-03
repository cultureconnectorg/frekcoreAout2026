import { strict as assert } from "node:assert";
import { test } from "node:test";
import { TechnicalEvidenceReportClient } from "../src/technicalEvidenceReportClient";
import { FetchLike } from "../src/registryClient";
import { NotFoundError } from "../src/errors";

test("generateReport posts subjectType/subjectId only and parses the real response shape", async () => {
  let capturedBody: unknown;
  const fetchImpl: FetchLike = async (input, init) => {
    assert.equal(new URL(input).pathname, "/api/v1/reports/technical-evidence");
    capturedBody = JSON.parse(init?.body as string);
    return new Response(
      JSON.stringify({ report_id: "rpt-1", subject_type: "frek_object", subject_id: "fk-1" }),
      { status: 200 }
    );
  };
  const client = new TechnicalEvidenceReportClient("https://frekcore.example.com", fetchImpl);
  const result = await client.generateReport({
    subjectType: "frek_object",
    subjectId: "fk-1",
    adminKey: "secret",
  });
  assert.equal(result.report_id, "rpt-1");
  assert.deepEqual(capturedBody, { subject_type: "frek_object", subject_id: "fk-1" });
});

test("verifyReport is public and returns shape-only integrity confirmation", async () => {
  const fetchImpl: FetchLike = async (input) => {
    assert.equal(new URL(input).pathname, "/api/v1/reports/technical-evidence/rpt-1/verify");
    return new Response(
      JSON.stringify({
        report_id: "rpt-1",
        report_hash: "abc123",
        integrity_verified: true,
        sections_summary: [{ kind: "proof", title: "Proof" }],
        legal_disclaimer: "This is a FREKCORE Technical Evidence Report...",
      }),
      { status: 200 }
    );
  };
  const client = new TechnicalEvidenceReportClient("https://frekcore.example.com", fetchImpl);
  const result = await client.verifyReport("rpt-1");
  assert.equal(result.integrity_verified, true);
});

test("verifyReport unknown id raises NotFoundError", async () => {
  const fetchImpl: FetchLike = async () =>
    new Response(JSON.stringify({ detail: "report_introuvable" }), { status: 404 });
  const client = new TechnicalEvidenceReportClient("https://frekcore.example.com", fetchImpl);
  await assert.rejects(() => client.verifyReport("does-not-exist"), NotFoundError);
});
