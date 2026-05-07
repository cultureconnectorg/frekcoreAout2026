/**
 * FREK Certified Seal — script standalone embeddable.
 *
 * Usage partenaire :
 *   <script src="https://frekcore.com/seal.js" data-frek-id="..." async></script>
 *
 * Optionnel :
 *   data-size="120"           Taille du seal en pixels (defaut 110)
 *   data-theme="light|dark"   Style visuel (defaut light)
 *   data-link="0|1"           Cliquable vers /verify (defaut 1)
 *
 * La cle publique est injectee par le serveur au moment de la livraison.
 */
(function () {
  "use strict";
  var FREK_PUB_B64 = "%%FREK_PUBLIC_KEY_B64%%";
  var ORIGIN = (function () {
    try {
      var u = new URL(document.currentScript.src);
      return u.origin;
    } catch (e) { return ""; }
  })();

  var script = document.currentScript;
  if (!script) return;
  var frekId = script.getAttribute("data-frek-id");
  if (!frekId) {
    console.warn("[FREK Seal] data-frek-id manquant sur la balise <script>");
    return;
  }
  var size = parseInt(script.getAttribute("data-size") || "110", 10);
  var theme = (script.getAttribute("data-theme") || "light").toLowerCase();
  var linkable = script.getAttribute("data-link") !== "0";

  // Container injecte juste apres la balise script
  var host = document.createElement("span");
  host.setAttribute("data-frek-seal", frekId);
  host.style.display = "inline-block";
  host.style.lineHeight = "0";
  host.style.verticalAlign = "middle";
  script.parentNode.insertBefore(host, script.nextSibling);

  // Attach shadow DOM pour eviter pollution CSS partenaire
  var root = host.attachShadow ? host.attachShadow({ mode: "open" }) : host;

  // ---------- Web Crypto helpers (mirror du verifier) ----------
  var enc = new TextEncoder();
  var subtle = (window.crypto && window.crypto.subtle) ? window.crypto.subtle : null;
  function canonicalJson(o) {
    if (o === null || typeof o !== "object") return JSON.stringify(o);
    if (Array.isArray(o)) return "[" + o.map(canonicalJson).join(",") + "]";
    return "{" + Object.keys(o).sort().map(function (k) { return JSON.stringify(k) + ":" + canonicalJson(o[k]); }).join(",") + "}";
  }
  function hexToBytes(h) {
    var out = new Uint8Array(h.length / 2);
    for (var i = 0; i < out.length; i++) out[i] = parseInt(h.substr(i * 2, 2), 16);
    return out;
  }
  function bytesToHex(b) {
    return Array.prototype.map.call(b, function (x) { return x.toString(16).padStart(2, "0"); }).join("");
  }
  function b64ToBytes(b64) {
    var bin = atob(b64);
    var out = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
  }
  function concat(a, b) {
    var o = new Uint8Array(a.length + b.length); o.set(a, 0); o.set(b, a.length); return o;
  }
  function sha256(b) { return subtle.digest("SHA-256", b).then(function (h) { return new Uint8Array(h); }); }
  function pair(l, r) { return sha256(concat(hexToBytes(l), hexToBytes(r))).then(bytesToHex); }
  function leaf(c) {
    return sha256(enc.encode(canonicalJson({ key: c.key, nonce: c.nonce, value: c.value }))).then(bytesToHex);
  }
  function rootFrom(leaves) {
    function step(cur) {
      if (cur.length <= 1) return Promise.resolve(cur[0]);
      var nxt = [];
      var p = Promise.resolve();
      for (var i = 0; i < cur.length; i += 2) {
        (function (i) {
          var l = cur[i]; var r = (i + 1 < cur.length) ? cur[i + 1] : cur[i];
          p = p.then(function () { return pair(l, r); }).then(function (h) { nxt.push(h); });
        })(i);
      }
      return p.then(function () { return step(nxt); });
    }
    return step(leaves.slice());
  }
  function verifyDoc(doc, pubB64) {
    if (!subtle) return Promise.resolve({ valid: false });
    var env = doc.envelope, sigB64 = doc.signature;
    if (!env || !sigB64) return Promise.resolve({ valid: false });
    return subtle.importKey("raw", b64ToBytes(pubB64), { name: "Ed25519" }, false, ["verify"])
      .then(function (pk) {
        return subtle.verify({ name: "Ed25519" }, pk, b64ToBytes(sigB64), enc.encode(canonicalJson(env)));
      })
      .then(function (sigOk) {
        if (!sigOk) return { valid: false, reason: "signature_invalid" };
        var leavesP = Promise.all((doc.claims || []).map(leaf));
        return leavesP.then(rootFrom).then(function (root) {
          if (root !== env.merkle_root) return { valid: false, reason: "merkle_mismatch" };
          return { valid: true, claimsCount: env.claims_count, frekId: env.frek_id };
        });
      })
      .catch(function (e) { return { valid: false, reason: e.message }; });
  }

  // ---------- Render seal SVG ----------
  function renderSeal(state) {
    var color = state.valid ? "#10b981" : (state.error ? "#dc2626" : "#94a3b8");
    var bg = theme === "dark" ? "#0a1520" : "#ffffff";
    var fg = theme === "dark" ? "#e2e8f0" : "#0a1520";
    var label = state.valid ? "Certifie" : (state.error ? "Erreur" : "Verification...");
    var svg =
      '<svg xmlns="http://www.w3.org/2000/svg" width="' + size + '" height="' + size + '" viewBox="0 0 110 110" role="img" aria-label="FREK Certified ' + label + '">' +
        '<defs><filter id="s" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="1.5"/></filter></defs>' +
        '<circle cx="55" cy="55" r="50" fill="' + bg + '" stroke="' + color + '" stroke-width="2"/>' +
        '<circle cx="55" cy="55" r="42" fill="none" stroke="' + color + '" stroke-width="0.5" stroke-dasharray="2 3" opacity="0.5"/>' +
        '<text x="55" y="20" text-anchor="middle" font-family="ui-monospace, monospace" font-size="7" fill="' + fg + '" letter-spacing="2">FREKCORE</text>' +
        '<text x="55" y="50" text-anchor="middle" font-family="serif" font-size="13" font-weight="700" fill="' + color + '">FREK</text>' +
        '<text x="55" y="64" text-anchor="middle" font-family="ui-monospace, monospace" font-size="6" fill="' + fg + '" letter-spacing="1">CERTIFIED</text>' +
        '<text x="55" y="78" text-anchor="middle" font-family="ui-monospace, monospace" font-size="5" fill="' + color + '">' + label.toUpperCase() + '</text>' +
        '<text x="55" y="92" text-anchor="middle" font-family="ui-monospace, monospace" font-size="4.5" fill="' + fg + '" opacity="0.6">Ed25519 / Merkle</text>' +
      '</svg>';

    var wrap = document.createElement(linkable ? "a" : "span");
    if (linkable) {
      wrap.href = ORIGIN + "/verify/" + encodeURIComponent(frekId);
      wrap.target = "_blank";
      wrap.rel = "noopener noreferrer";
      wrap.title = "FREK Certified — verifier l'authenticite";
    }
    wrap.style.display = "inline-block";
    wrap.style.lineHeight = "0";
    wrap.style.textDecoration = "none";
    wrap.innerHTML = svg;
    if (root.firstChild) root.replaceChild(wrap, root.firstChild);
    else root.appendChild(wrap);
  }

  renderSeal({ valid: false, error: false });

  // Fetch passport + verify offline
  Promise.all([
    fetch(ORIGIN + "/api/v1/passport/" + encodeURIComponent(frekId)).then(function (r) {
      if (!r.ok) throw new Error("passport_" + r.status);
      return r.json();
    }),
  ])
    .then(function (results) {
      return verifyDoc(results[0], FREK_PUB_B64);
    })
    .then(function (verdict) {
      renderSeal({ valid: verdict.valid, error: !verdict.valid });
    })
    .catch(function () {
      renderSeal({ valid: false, error: true });
    });
})();
