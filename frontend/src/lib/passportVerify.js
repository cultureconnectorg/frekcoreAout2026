/**
 * FREK Passport — Verifier offline (frontend mirror).
 * Source de verite : /app/verifier/js/verify_passport.js
 * Aucune dependance, utilise Web Crypto API (Chrome 113+, Firefox 130+, Safari 17+).
 */

const enc = new TextEncoder();
const subtle = (typeof crypto !== "undefined" && crypto.subtle) ? crypto.subtle : null;

function canonicalJson(obj) {
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
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

async function sha256(bytes) {
  return new Uint8Array(await subtle.digest("SHA-256", bytes));
}

function concat(a, b) {
  const out = new Uint8Array(a.length + b.length);
  out.set(a, 0); out.set(b, a.length);
  return out;
}

async function leafHex(c) {
  return bytesToHex(await sha256(enc.encode(canonicalJson({ key: c.key, nonce: c.nonce, value: c.value }))));
}

async function pairHex(l, r) {
  return bytesToHex(await sha256(concat(hexToBytes(l), hexToBytes(r))));
}

async function rootFromLeaves(leaves) {
  let cur = [...leaves];
  while (cur.length > 1) {
    const nxt = [];
    for (let i = 0; i < cur.length; i += 2) {
      const l = cur[i];
      const r = (i + 1 < cur.length) ? cur[i + 1] : cur[i];
      nxt.push(await pairHex(l, r));
    }
    cur = nxt;
  }
  return cur[0];
}

async function verifyPath(leaf, path, root) {
  let cur = leaf;
  for (const step of path) {
    if (step.side === "left") cur = await pairHex(step.hash, cur);
    else if (step.side === "right") cur = await pairHex(cur, step.hash);
    else return false;
  }
  return cur === root;
}

export async function verifyPassport(doc, pubKeyB64) {
  if (!subtle) {
    return { valid: false, mode: doc.disclosure || "full", errors: ["webcrypto_unavailable"], claims: [] };
  }
  const errors = [];
  const env = doc.envelope;
  const sigB64 = doc.signature;
  const claims = doc.claims || [];
  const mode = doc.disclosure || "full";

  if (!env || !sigB64) return { valid: false, mode, errors: ["missing envelope or signature"], claims: [] };

  try {
    const pub = await subtle.importKey("raw", b64ToBytes(pubKeyB64), { name: "Ed25519" }, false, ["verify"]);
    const sig = b64ToBytes(sigB64);
    const ok = await subtle.verify({ name: "Ed25519" }, pub, sig, enc.encode(canonicalJson(env)));
    if (!ok) errors.push("signature_invalid");
  } catch (e) {
    errors.push("signature_decode_error:" + e.message);
  }

  const expectedRoot = env.merkle_root;
  if (mode === "full") {
    if (env.claims_count !== claims.length) errors.push("claims_count_mismatch");
    if (claims.length === 0) errors.push("no_claims");
    else {
      const leaves = [];
      for (const c of claims) leaves.push(await leafHex(c));
      const actual = await rootFromLeaves(leaves);
      if (actual !== expectedRoot) errors.push("merkle_root_mismatch");
    }
  } else {
    for (const c of claims) {
      if (!c.merkle_path) { errors.push(`claim_${c.key}_missing_path`); continue; }
      const ok = await verifyPath(await leafHex(c), c.merkle_path, expectedRoot);
      if (!ok) errors.push(`claim_${c.key}_path_invalid`);
    }
  }

  return {
    valid: errors.length === 0,
    mode,
    errors,
    envelope: env,
    claims: claims.map(c => ({ key: c.key, value: c.value })),
  };
}
