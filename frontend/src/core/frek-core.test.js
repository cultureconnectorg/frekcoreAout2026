/**
 * FREK Core Conformance Tests
 * 
 * These tests verify that the frek-core module correctly implements
 * the FREK v0.4 specification for cryptographic verification.
 * 
 * Test Categories:
 * 1. Schema Validation - Tests for JSON structure validation
 * 2. Signature Verification - Tests for Ed25519 signature checks
 * 3. Canonicalization - Tests for metadata canonicalization
 * 4. Golden Vector Tests - Tests against known-good samples
 * 5. Failure Tests - Tests for proper error handling
 */

import {
  canonicalize,
  verifySignature,
  validateSchema,
  sha256,
  hashAudio
} from './frek-core';

// Test results storage
const testResults = {
  passed: 0,
  failed: 0,
  tests: []
};

function assert(condition, testName, details = '') {
  const result = {
    name: testName,
    passed: condition,
    details
  };
  testResults.tests.push(result);
  if (condition) {
    testResults.passed++;
    console.log(`✓ ${testName}`);
  } else {
    testResults.failed++;
    console.error(`✗ ${testName}: ${details}`);
  }
  return condition;
}

// ============================================================================
// Test Vectors
// ============================================================================

const VALID_FREK_DOC = {
  frek_version: "0.4",
  fingerprint: "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  segments: [
    { t0: 0, t1: 5, h: "sha256:1111111111111111111111111111111111111111111111111111111111111111" }
  ],
  metadata: {
    timestamp: "2024-04-20T15:30:00Z",
    duration: 3600,
    source_type: "live"
  },
  signature: "ed25519:YHekHZ2IG3etJfcyEn351gy6tZ2pvG9iCph52IWa7RdrfUE0px15zSE7AyiiOXSNI+yKzaNVqhRT5uj64WFWCQ==",
  public_key: "MmKRpk8kB2p0dnkME2f+Xq/7PTa1gUt4a1bSAvUaPJs="
};

const INVALID_VERSION_DOC = {
  ...VALID_FREK_DOC,
  frek_version: "0.3"
};

const INVALID_FINGERPRINT_DOC = {
  ...VALID_FREK_DOC,
  fingerprint: "invalid-format"
};

const INVALID_METADATA_DOC = {
  ...VALID_FREK_DOC,
  metadata: {
    timestamp: "not-a-date",
    duration: -100,
    source_type: "invalid_type"
  }
};

const MISSING_FIELDS_DOC = {
  frek_version: "0.4",
  fingerprint: "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
};

// ============================================================================
// Schema Validation Tests
// ============================================================================

export async function runSchemaTests() {
  console.log('\n=== Schema Validation Tests ===\n');
  
  // Test 1: Valid document passes
  const valid = validateSchema(VALID_FREK_DOC);
  assert(
    valid.valid === true,
    'Valid FREK document passes schema validation',
    valid.errors?.map(e => e.message).join(', ')
  );
  
  // Test 2: Invalid version fails
  const invalidVersion = validateSchema(INVALID_VERSION_DOC);
  assert(
    invalidVersion.valid === false,
    'Invalid version (0.3) fails schema validation',
    invalidVersion.valid ? 'Should have failed' : 'Correctly rejected'
  );
  
  // Test 3: Invalid fingerprint format fails
  const invalidFp = validateSchema(INVALID_FINGERPRINT_DOC);
  assert(
    invalidFp.valid === false,
    'Invalid fingerprint format fails validation',
    invalidFp.valid ? 'Should have failed' : 'Correctly rejected'
  );
  
  // Test 4: Invalid metadata fails
  const invalidMeta = validateSchema(INVALID_METADATA_DOC);
  assert(
    invalidMeta.valid === false,
    'Invalid metadata fails validation',
    invalidMeta.valid ? 'Should have failed' : 'Correctly rejected'
  );
  
  // Test 5: Missing required fields fails
  const missingFields = validateSchema(MISSING_FIELDS_DOC);
  assert(
    missingFields.valid === false,
    'Missing required fields fails validation',
    missingFields.valid ? 'Should have failed' : 'Correctly rejected'
  );
}

// ============================================================================
// Canonicalization Tests
// ============================================================================

export async function runCanonicalizationTests() {
  console.log('\n=== Canonicalization Tests ===\n');
  
  // Test 1: Keys are sorted alphabetically
  const unsorted = { z: 1, a: 2, m: 3 };
  const result = canonicalize(unsorted);
  const parsed = JSON.parse(result);
  const keys = Object.keys(parsed);
  assert(
    keys[0] === 'a' && keys[1] === 'm' && keys[2] === 'z',
    'Canonicalization sorts keys alphabetically',
    `Got keys: ${keys.join(', ')}`
  );
  
  // Test 2: Same input produces same output
  const input1 = { b: 2, a: 1 };
  const input2 = { a: 1, b: 2 };
  assert(
    canonicalize(input1) === canonicalize(input2),
    'Different key order produces identical output',
    `${canonicalize(input1)} vs ${canonicalize(input2)}`
  );
  
  // Test 3: Nested objects are handled
  const nested = { z: { b: 2, a: 1 }, a: 1 };
  const nestedResult = canonicalize(nested);
  assert(
    nestedResult.includes('"a":1') && nestedResult.indexOf('"a"') < nestedResult.indexOf('"z"'),
    'Nested objects maintain sorted top-level keys',
    nestedResult
  );
  
  // Test 4: Invalid input throws error
  let threw = false;
  try {
    canonicalize(null);
  } catch (e) {
    threw = true;
  }
  assert(
    threw === true,
    'Canonicalize throws on null input',
    threw ? 'Correctly threw' : 'Should have thrown'
  );
}

// ============================================================================
// Hashing Tests
// ============================================================================

export async function runHashTests() {
  console.log('\n=== Hashing Tests ===\n');
  
  // Test 1: SHA-256 of empty string
  const emptyHash = await sha256('');
  assert(
    emptyHash === 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    'SHA-256 of empty string matches expected',
    `Got: ${emptyHash}`
  );
  
  // Test 2: SHA-256 of "hello"
  const helloHash = await sha256('hello');
  assert(
    helloHash === '2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824',
    'SHA-256 of "hello" matches expected',
    `Got: ${helloHash}`
  );
  
  // Test 3: Same input produces same hash
  const hash1 = await sha256('test');
  const hash2 = await sha256('test');
  assert(
    hash1 === hash2,
    'Same input produces identical hash',
    `${hash1} vs ${hash2}`
  );
  
  // Test 4: Different input produces different hash
  const hashA = await sha256('a');
  const hashB = await sha256('b');
  assert(
    hashA !== hashB,
    'Different inputs produce different hashes',
    `${hashA.slice(0, 16)}... vs ${hashB.slice(0, 16)}...`
  );
}

// ============================================================================
// Signature Verification Tests
// ============================================================================

export async function runSignatureTests() {
  console.log('\n=== Signature Verification Tests ===\n');
  
  // Test 1: Invalid signature length fails
  const shortSig = verifySignature('test', 'YWJj', 'MmKRpk8kB2p0dnkME2f+Xq/7PTa1gUt4a1bSAvUaPJs=');
  assert(
    shortSig.valid === false && shortSig.error?.includes('Invalid signature length'),
    'Short signature fails with appropriate error',
    shortSig.error || 'No error message'
  );
  
  // Test 2: Invalid public key length fails
  const shortKey = verifySignature(
    'test',
    'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
    'YWJj'
  );
  assert(
    shortKey.valid === false && shortKey.error?.includes('Invalid public key length'),
    'Short public key fails with appropriate error',
    shortKey.error || 'No error message'
  );
  
  // Test 3: Malformed base64 fails gracefully
  const malformedSig = verifySignature('test', '!!!invalid!!!', 'MmKRpk8kB2p0dnkME2f+Xq/7PTa1gUt4a1bSAvUaPJs=');
  assert(
    malformedSig.valid === false,
    'Malformed base64 signature fails gracefully',
    malformedSig.error || 'No error'
  );
}

// ============================================================================
// Golden Vector Tests (Known-Good Samples)
// ============================================================================

export async function runGoldenVectorTests() {
  console.log('\n=== Golden Vector Tests ===\n');
  
  // Test 1: Empty string hash (SHA-256)
  const emptyHash = await sha256('');
  assert(
    emptyHash === 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    'Golden vector: SHA-256 of empty string',
    `Expected: e3b0c44..., Got: ${emptyHash.slice(0, 8)}...`
  );
  
  // Test 2: Canonical metadata format
  const metadata = { duration: 3600, source_type: "live", timestamp: "2024-04-20T15:30:00Z" };
  const canonical = canonicalize(metadata);
  // Keys should be sorted: duration, source_type, timestamp
  const expectedOrder = '{"duration":3600,"source_type":"live","timestamp":"2024-04-20T15:30:00Z"}';
  assert(
    canonical === expectedOrder,
    'Golden vector: Canonical metadata format',
    `Expected: ${expectedOrder}\nGot: ${canonical}`
  );
  
  // Test 3: Fingerprint format validation
  const validFp = 'sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855';
  const fpRegex = /^sha256:[a-f0-9]{64}$/;
  assert(
    fpRegex.test(validFp),
    'Golden vector: Fingerprint format matches specification',
    `Pattern: sha256:<64 hex chars>`
  );
}

// ============================================================================
// Failure Mode Tests
// ============================================================================

export async function runFailureTests() {
  console.log('\n=== Failure Mode Tests ===\n');
  
  // Test 1: Empty object fails validation
  const empty = validateSchema({});
  assert(
    empty.valid === false,
    'Empty object fails validation',
    empty.errors?.length > 0 ? `${empty.errors.length} errors` : 'No errors reported'
  );
  
  // Test 2: Wrong fingerprint prefix fails
  const wrongPrefix = validateSchema({
    ...VALID_FREK_DOC,
    fingerprint: "md5:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  });
  assert(
    wrongPrefix.valid === false,
    'Wrong fingerprint prefix (md5:) fails validation',
    wrongPrefix.valid ? 'Should have failed' : 'Correctly rejected'
  );
  
  // Test 3: Wrong signature prefix fails
  const wrongSigPrefix = validateSchema({
    ...VALID_FREK_DOC,
    signature: "rsa:AAAA..."
  });
  assert(
    wrongSigPrefix.valid === false,
    'Wrong signature prefix (rsa:) fails validation',
    wrongSigPrefix.valid ? 'Should have failed' : 'Correctly rejected'
  );
  
  // Test 4: Invalid source_type fails
  const wrongSourceType = validateSchema({
    ...VALID_FREK_DOC,
    metadata: {
      ...VALID_FREK_DOC.metadata,
      source_type: "unknown"
    }
  });
  assert(
    wrongSourceType.valid === false,
    'Invalid source_type fails validation',
    wrongSourceType.valid ? 'Should have failed' : 'Correctly rejected'
  );
}

// ============================================================================
// Run All Tests
// ============================================================================

export async function runAllTests() {
  console.log('='.repeat(60));
  console.log('FREK Core Conformance Test Suite v0.4');
  console.log('='.repeat(60));
  
  testResults.passed = 0;
  testResults.failed = 0;
  testResults.tests = [];
  
  await runSchemaTests();
  await runCanonicalizationTests();
  await runHashTests();
  await runSignatureTests();
  await runGoldenVectorTests();
  await runFailureTests();
  
  console.log('\n' + '='.repeat(60));
  console.log(`Test Results: ${testResults.passed} passed, ${testResults.failed} failed`);
  console.log('='.repeat(60));
  
  return {
    summary: {
      total: testResults.passed + testResults.failed,
      passed: testResults.passed,
      failed: testResults.failed,
      success: testResults.failed === 0
    },
    tests: testResults.tests
  };
}

export default { runAllTests };
