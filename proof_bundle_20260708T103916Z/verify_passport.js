/**
 * FREK Passport — Verifier offline standalone (ES module).
 *
 * Aucune dependance externe. Utilise Web Crypto API (built-in).
 * - Navigateur : Chrome 113+, Firefox 130+, Safari 17+
 * - Node : 20+ (avec --experimental-global-webcrypto par defaut a partir de 19)
 *
 * Usage :
 *   import { verifyPassport } from './verify_passport.js';
 *   const result = await verifyPassport(passportDoc, publicKeyRawB64);
 *   // => { valid: true, mode: 'full'|'partial', errors: [], envelope, claims }
 *
 * Specification : voir /api/v1/spec/v1.0.0 section passport.
 */

const enc = new TextEncoder();
const subtle = (typeof crypto !== "undefined" && crypto.subtle) ? crypto.subtle : null;
if (!subtle) {
  throw new Error("FREK verifier: Web Crypto API indisponible (Node 20+ ou navigateur moderne requis)");
}

// ---------- helpers ----------

function canonicalJson(obj) {
  // JSON canonique : tri alphabetique des cles, separateurs minimaux
  if (obj === null || typeof obj !== "object") return JSON.stringify(obj);
  if (Array.isArray(obj)) return "[" + obj.map(canonicalJson).join(",") + "]";
  const keys = Object.keys(obj).sort();
  return "{" + keys.map(k => JSON.stringify(k) + ":" + canonicalJson(obj[k])).join(",") + "}";
}

function hexToBytes(hex) {
  const out = new Uint8Array(hex.length / 2);
  for (let i = 0; i < out.length; i++) out[i] = parseInt(hex.substr(i * 2, 2), 16);
  return out;
}

function bytesToHex(bytes) {
  return Array.from(bytes, b => b.toString(16).padStart(2, "0")).join("");
}

function b64ToBytes(b64) {
  if (typeof Buffer !== "undefined") return new Uint8Array(Buffer.from(b64, "base64"));
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

async function sha256Bytes(bytes) {
  return new Uint8Array(await subtle.digest("SHA-256", bytes));
}

function concatBytes(a, b) {
  const out = new Uint8Array(a.length + b.length);
  out.set(a, 0);
  out.set(b, a.length);
  return out;
}

async function claimLeafHex(claim) {
  const payload = enc.encode(canonicalJson({ key: claim.key, nonce: claim.nonce, value: claim.value }));
  return bytesToHex(await sha256Bytes(payload));
}

async function hashPairHex(leftHex, rightHex) {
  const combined = concatBytes(hexToBytes(leftHex), hexToBytes(rightHex));
  return bytesToHex(await sha256Bytes(combined));
}

async function merkleRootFromLeaves(leaves) {
  let cur = [...leaves];
  while (cur.length > 1) {
    const nxt = [];
    for (let i = 0; i < cur.length; i += 2) {
      const l = cur[i];
      const r = (i + 1 < cur.length) ? cur[i + 1] : cur[i];
      nxt.push(await hashPairHex(l, r));
    }
    cur = nxt;
  }
  return cur[0];
}

async function verifyMerklePath(leafHex, path, expectedRoot) {
  let cur = leafHex;
  for (const step of path) {
    if (step.side === "left") cur = await hashPairHex(step.hash, cur);
    else if (step.side === "right") cur = await hashPairHex(cur, step.hash);
    else return false;
  }
  return cur === expectedRoot;
}

async function importEd25519PublicKey(rawB64) {
  const raw = b64ToBytes(rawB64);
  return await subtle.importKey("raw", raw, { name: "Ed25519" }, false, ["verify"]);
}

// ---------- API publique ----------

/**
 * @param {object} doc       passport.json (full ou partial)
 * @param {string} pubKeyB64 cle publique raw 32-bytes en base64 (champ public_key_raw_b64)
 * @returns {Promise<{valid:boolean, mode:string, errors:string[], envelope?:object, claims?:object[]}>}
 */
export async function verifyPassport(doc, pubKeyB64) {
  const errors = [];
  const envelope = doc.envelope;
  const sigB64 = doc.signature;
  const claims = doc.claims || [];
  const mode = doc.disclosure || "full";

  if (!envelope || !sigB64) {
    return { valid: false, mode, errors: ["missing envelope or signature"], claims: [] };
  }

  // 1. Verification Ed25519 sur canonical_json(envelope)
  try {
    const pubKey = await importEd25519PublicKey(pubKeyB64);
    const sig = b64ToBytes(sigB64);
    const message = enc.encode(canonicalJson(envelope));
    const ok = await subtle.verify({ name: "Ed25519" }, pubKey, sig, message);
    if (!ok) errors.push("signature_invalid");
  } catch (e) {
    errors.push(`signature_decode_error: ${e.message}`);
  }

  const expectedRoot = envelope.merkle_root;

  if (mode === "full") {
    if (envelope.claims_count !== claims.length) errors.push("claims_count_mismatch");
    if (claims.length === 0) {
      errors.push("no_claims");
    } else {
      const leaves = [];
      for (const c of claims) leaves.push(await claimLeafHex(c));
      const actual = await merkleRootFromLeaves(leaves);
      if (actual !== expectedRoot) errors.push("merkle_root_mismatch");
    }
  } else {
    for (const c of claims) {
      if (!c.merkle_path) {
        errors.push(`claim_${c.key}_missing_path`);
        continue;
      }
      const leaf = await claimLeafHex(c);
      const ok = await verifyMerklePath(leaf, c.merkle_path, expectedRoot);
      if (!ok) errors.push(`claim_${c.key}_path_invalid`);
    }
  }

  return {
    valid: errors.length === 0,
    mode,
    errors,
    envelope,
    claims: claims.map(c => ({ key: c.key, value: c.value })),
  };
}
