/**
 * PassportPanel — affiche le passeport FREK signe Ed25519, verifie en live
 * via Web Crypto API cote navigateur, et propose son telechargement.
 *
 * Aucun secret expose. La cle publique sert UNIQUEMENT a la verification.
 */
import { useEffect, useMemo, useState } from "react";
import { QRCodeSVG } from "qrcode.react";
import { verifyPassport } from "../lib/passportVerify";

const API_URL = import.meta.env.VITE_BACKEND_URL || "";

export default function PassportPanel({ frekId }) {
  const [passport, setPassport] = useState(null);
  const [pubKeyB64, setPubKeyB64] = useState(null);
  const [verdict, setVerdict] = useState(null); // {valid, mode, errors, claims}
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        setLoading(true);
        const [pRes, kRes] = await Promise.all([
          fetch(`${API_URL}/api/v1/passport/${frekId}`),
          fetch(`${API_URL}/api/v1/passport/key`),
        ]);
        if (!pRes.ok) throw new Error(`passport ${pRes.status}`);
        if (!kRes.ok) throw new Error(`key ${kRes.status}`);
        const p = await pRes.json();
        const k = await kRes.json();
        if (!alive) return;
        setPassport(p);
        setPubKeyB64(k.public_key_raw_b64);
        const v = await verifyPassport(p, k.public_key_raw_b64);
        if (!alive) return;
        setVerdict(v);
      } catch (e) {
        if (alive) setError(e.message);
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, [frekId]);

  const passportBlobUrl = useMemo(() => {
    if (!passport) return null;
    const blob = new Blob([JSON.stringify(passport, null, 2)], { type: "application/json" });
    return URL.createObjectURL(blob);
  }, [passport]);

  useEffect(() => () => { if (passportBlobUrl) URL.revokeObjectURL(passportBlobUrl); }, [passportBlobUrl]);

  if (loading) {
    return (
      <div data-testid="passport-panel-loading" className="rounded-xl border border-[#2cc4f5]/20 bg-[#0a1520]/40 p-4 sm:p-5">
        <div className="font-mono text-[10px] text-[#2cc4f5]/60 uppercase tracking-wider">Verification cryptographique en cours...</div>
      </div>
    );
  }

  if (error || !passport || !verdict) {
    return (
      <div data-testid="passport-panel-error" className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-4 sm:p-5">
        <div className="font-mono text-[10px] text-amber-400/80 uppercase tracking-wider">
          Passeport indisponible {error ? `· ${error}` : ""}
        </div>
      </div>
    );
  }

  const valid = verdict.valid;
  const claims = verdict.claims || [];

  return (
    <div
      data-testid="passport-panel"
      className={`rounded-xl border p-4 sm:p-5 bg-gradient-to-br ${
        valid
          ? "from-emerald-500/10 to-[#0a1520]/80 border-emerald-500/30"
          : "from-red-500/10 to-[#0a1520]/80 border-red-500/40"
      }`}
    >
      <div className="flex items-center gap-2 mb-3 sm:mb-4">
        <div className={`w-7 h-7 sm:w-8 sm:h-8 rounded-full border flex items-center justify-center ${
          valid ? "bg-emerald-500/20 border-emerald-400/40 text-emerald-300" : "bg-red-500/20 border-red-400/40 text-red-300"
        }`}>
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            {valid
              ? <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
              : <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />}
          </svg>
        </div>
        <div className="flex-1">
          <div className={`font-mono text-[10px] uppercase tracking-wider ${valid ? "text-emerald-300" : "text-red-300"}`}>
            Passeport souverain · Ed25519 + Merkle
          </div>
          <div className="font-mono text-[9px] text-white/40">
            Verifie offline cote navigateur · aucune donnee envoyee a FREKCORE
          </div>
        </div>
        <span
          data-testid="passport-verdict"
          className={`px-2.5 py-1 rounded-full font-mono text-[10px] uppercase tracking-wider ${
            valid ? "bg-emerald-500/20 text-emerald-200 border border-emerald-400/40" : "bg-red-500/20 text-red-200 border border-red-400/40"
          }`}
        >
          {valid ? "Valide" : "Invalide"}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-3">
        <div>
          <div className="font-mono text-[9px] text-white/40 uppercase tracking-wider mb-1">Signature Ed25519</div>
          <div data-testid="passport-sig-status" className={`font-mono text-xs ${verdict.errors.includes("signature_invalid") ? "text-red-300" : "text-emerald-300"}`}>
            {verdict.errors.includes("signature_invalid") ? "Echouee" : "OK"}
          </div>
        </div>
        <div>
          <div className="font-mono text-[9px] text-white/40 uppercase tracking-wider mb-1">Racine Merkle</div>
          <div data-testid="passport-merkle-status" className={`font-mono text-xs ${verdict.errors.some(e => e.includes("merkle") || e.includes("path")) ? "text-red-300" : "text-emerald-300"}`}>
            {verdict.errors.some(e => e.includes("merkle") || e.includes("path")) ? "Echec" : "OK"}
          </div>
        </div>
      </div>

      <div className="mb-3">
        <div className="font-mono text-[9px] text-white/40 uppercase tracking-wider mb-1">
          Claims certifies ({claims.length})
        </div>
        <ul data-testid="passport-claims" className="space-y-1 max-h-44 overflow-auto">
          {claims.map((c, i) => (
            <li key={i} data-testid={`passport-claim-${c.key}`} className="flex items-center gap-2 font-mono text-[11px]">
              <svg className="w-3 h-3 text-emerald-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
              </svg>
              <span className="text-white/40 w-32 shrink-0 truncate">{c.key}</span>
              <span className="text-white/80 truncate">
                {typeof c.value === "object" ? JSON.stringify(c.value) : String(c.value ?? "—")}
              </span>
            </li>
          ))}
        </ul>
      </div>

      <details className="mb-3">
        <summary className="font-mono text-[10px] text-white/40 uppercase tracking-wider cursor-pointer hover:text-white/60">
          Detail cryptographique
        </summary>
        <div className="mt-2 space-y-1 font-mono text-[10px] text-white/50 break-all">
          <div><span className="text-white/30">Cle publique :</span> {pubKeyB64}</div>
          <div><span className="text-white/30">Racine Merkle :</span> {passport.envelope.merkle_root}</div>
          <div><span className="text-white/30">Issued at :</span> {passport.envelope.issued_at}</div>
        </div>
      </details>

      <div className="flex flex-wrap items-center gap-3 pt-3 border-t border-white/10">
        {passportBlobUrl && (
          <a
            href={passportBlobUrl}
            download={`frek-passport-${frekId}.json`}
            data-testid="passport-download"
            className="px-3 py-1.5 bg-emerald-500/10 border border-emerald-400/40 text-emerald-200 font-mono text-[10px] uppercase tracking-wider rounded hover:bg-emerald-500/20 transition-all"
          >
            Telecharger passport.json
          </a>
        )}
        <a
          href={`/verifier?lang=python`}
          target="_blank"
          rel="noopener noreferrer"
          data-testid="passport-download-verifier"
          className="px-3 py-1.5 border border-white/20 text-white/60 font-mono text-[10px] uppercase tracking-wider rounded hover:border-white/40 hover:text-white/80 transition-all"
        >
          Verifier offline (Python)
        </a>
        {passportBlobUrl && (
          <div className="ml-auto p-2 bg-white rounded">
            <QRCodeSVG value={passportBlobUrl} size={70} level="M" fgColor="#0a1520" />
          </div>
        )}
      </div>
    </div>
  );
}
