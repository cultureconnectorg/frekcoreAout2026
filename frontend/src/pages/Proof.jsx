/**
 * FREK — Page Proof Publique /proof/:hash
 *
 * Affiche une preuve d'ancrage Bitcoin lisible par n'importe qui :
 *  - Block hash + height + payload_type + payload_id
 *  - Si geo_anchor : Plus Code humain + image satellite EOX du jour
 *  - OTS proof status (pending / upgraded / confirmed Bitcoin)
 *  - QR code de cette page elle-meme (partageable)
 *
 * Lecture seule. Consomme uniquement `GET /api/v1/notary/blocks` existant.
 */
import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { QRCodeSVG } from 'qrcode.react';

const API_URL = import.meta.env.VITE_BACKEND_URL || '';
const ORIGIN = typeof window !== 'undefined' ? window.location.origin : '';

function BackgroundDecor() {
  return (
    <>
      <div aria-hidden className="absolute -top-32 -right-32 w-[500px] h-[500px] bg-gradient-to-br from-[#2cc4f5] to-[#06b6d4] rounded-full blur-3xl opacity-30" />
      <div aria-hidden className="absolute -bottom-40 -left-40 w-[600px] h-[600px] bg-gradient-to-tr from-[#0ea5e9] to-[#2cc4f5] rounded-full blur-3xl opacity-25" />
    </>
  );
}

function CopyButton({ value, testid }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => {
        navigator.clipboard?.writeText(value);
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      }}
      data-testid={testid}
      className="font-mono text-[9px] text-slate-400 hover:text-[#0ea5e9] uppercase tracking-widest transition"
    >
      {copied ? '✓ copié' : 'copier'}
    </button>
  );
}

export default function Proof() {
  const { hash } = useParams();
  const [block, setBlock] = useState(null);
  const [otsStatus, setOtsStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState(null);

  // Recherche block par hash via /api/v1/notary/blocks (deja existant)
  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true); setError(null); setNotFound(false);
      try {
        // Charge les 1000 derniers blocks et filtre par hash
        const r = await fetch(`${API_URL}/api/v1/notary/blocks?limit=1000`);
        if (!r.ok) throw new Error('blocks_unavailable');
        const blocks = await r.json();
        if (cancelled) return;
        const found = (blocks || []).find((b) => b.block_hash === hash || b.block_hash?.startsWith(hash));
        if (!found) { setNotFound(true); return; }
        setBlock(found);
        // Tente le statut OTS via /api/v1/notary/proof/{payload_id}/ots
        try {
          const o = await fetch(`${API_URL}/api/v1/notary/proof/${encodeURIComponent(found.payload_id)}/ots`);
          if (o.ok) setOtsStatus(await o.json());
        } catch { /* ots optional */ }
      } catch (e) {
        if (!cancelled) setError('Backend injoignable');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    if (hash) load();
    return () => { cancelled = true; };
  }, [hash]);

  const geo = block?.payload_data?.geo;
  const satWitness = block?.payload_data?.satellite_witness;
  const proofUrl = `${ORIGIN}/proof/${hash}`;
  const isGeoAnchor = block?.payload_type === 'geo_anchor';

  // Construit l'URL satellite EOX a partir du payload (tile x,y,z connus)
  const eoxImg = useMemo(() => {
    if (!satWitness?.eox_s2) return null;
    const { x, y, zoom } = satWitness.eox_s2;
    return `${API_URL}/api/geo/satellite?lat=${geo?.lat ?? 0}&lon=${geo?.lon ?? 0}&provider=eox_s2&zoom=${zoom}`;
  }, [satWitness, geo]);

  const gibsImg = useMemo(() => {
    if (!satWitness?.nasa_gibs) return null;
    const { zoom } = satWitness.nasa_gibs;
    return `${API_URL}/api/geo/satellite?lat=${geo?.lat ?? 0}&lon=${geo?.lon ?? 0}&provider=gibs&zoom=${zoom}`;
  }, [satWitness, geo]);

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-800 relative overflow-hidden">
      <BackgroundDecor />

      <header className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 pt-6">
        <div className="bg-white/70 backdrop-blur-2xl rounded-2xl border border-white/60 shadow-lg shadow-slate-200/50 px-4 sm:px-6 h-14 sm:h-16 flex items-center justify-between">
          <Link to="/accueil" data-testid="proof-home-link" className="flex items-center gap-2">
            <span className="font-display text-xl tracking-wider bg-gradient-to-r from-[#2cc4f5] to-[#0ea5e9] bg-clip-text text-transparent font-semibold">FREK</span>
          </Link>
          <span className="font-mono text-[10px] text-slate-400 uppercase tracking-widest">Preuve d'ancrage Bitcoin</span>
        </div>
      </header>

      <main className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 py-10 sm:py-14">
        {loading && (
          <div className="text-center py-20" data-testid="proof-loading">
            <div className="w-10 h-10 mx-auto border-2 border-slate-200 border-t-[#2cc4f5] rounded-full animate-spin mb-4" />
            <p className="font-mono text-xs text-[#0ea5e9]">Vérification en cours...</p>
          </div>
        )}

        {!loading && error && (
          <div data-testid="proof-error" className="rounded-lg p-3 bg-red-50 border border-red-200 font-mono text-[11px] text-red-600">
            {error}
          </div>
        )}

        {!loading && notFound && (
          <div className="text-center py-20" data-testid="proof-not-found">
            <h1 className="font-display text-3xl text-slate-800 mb-3">Preuve introuvable</h1>
            <p className="font-mono text-sm text-slate-400 mb-8">
              Aucun bloc FREK-Chain ne correspond à ce hash.
            </p>
            <Link to="/explorer" className="inline-block px-5 py-3 bg-gradient-to-r from-[#2cc4f5] to-[#0ea5e9] text-white font-mono text-xs uppercase tracking-wider rounded-xl shadow-lg transition-all font-semibold">
              Explorer FREK-Chain
            </Link>
          </div>
        )}

        {!loading && block && (
          <>
            <div className="mb-8">
              <div className="font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest mb-2">Notarisation souveraine</div>
              <h1 data-testid="proof-title" className="font-display text-3xl sm:text-4xl text-slate-800">
                Preuve d'existence
              </h1>
              <p className="font-mono text-sm text-slate-500 mt-2 max-w-2xl">
                Bloc #{block.height} de la FREK-Chain — ancré sur Bitcoin via OpenTimestamps.
                Vérifiable par n'importe quel tiers, à perpétuité.
              </p>
            </div>

            {/* Bloc principal */}
            <section data-testid="proof-block" className="bg-white/70 backdrop-blur-2xl border border-white/60 rounded-2xl p-5 sm:p-6 shadow-lg shadow-slate-200/40 mb-6">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
                <div>
                  <div className="font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest">Block #</div>
                  <div data-testid="proof-height" className="font-display text-2xl text-slate-800 tabular-nums mt-1">{block.height}</div>
                </div>
                <div>
                  <div className="font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest">Type</div>
                  <div data-testid="proof-payload-type" className="font-mono text-sm text-slate-800 mt-1">{block.payload_type}</div>
                </div>
                <div>
                  <div className="font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest">Ancré le</div>
                  <div data-testid="proof-timestamp" className="font-mono text-xs text-slate-700 mt-1">{new Date(block.timestamp).toLocaleString('fr-FR')}</div>
                </div>
              </div>

              <div className="space-y-3 border-t border-slate-100 pt-4">
                <div>
                  <div className="flex items-center justify-between">
                    <div className="font-mono text-[10px] text-slate-400 uppercase tracking-widest">Block hash</div>
                    <CopyButton value={block.block_hash} testid="proof-copy-hash" />
                  </div>
                  <code data-testid="proof-block-hash" className="font-mono text-xs text-slate-700 break-all block mt-1">{block.block_hash}</code>
                </div>
                <div>
                  <div className="flex items-center justify-between">
                    <div className="font-mono text-[10px] text-slate-400 uppercase tracking-widest">Payload ID</div>
                    <CopyButton value={block.payload_id} testid="proof-copy-payload" />
                  </div>
                  <code className="font-mono text-xs text-slate-700 break-all block mt-1">{block.payload_id}</code>
                </div>
                <div>
                  <div className="font-mono text-[10px] text-slate-400 uppercase tracking-widest">Payload hash</div>
                  <code className="font-mono text-xs text-slate-700 break-all block mt-1">{block.payload_hash}</code>
                </div>
              </div>
            </section>

            {/* Status OTS Bitcoin */}
            <section data-testid="proof-ots" className="bg-white/70 backdrop-blur-2xl border border-white/60 rounded-2xl p-5 sm:p-6 shadow-md mb-6">
              <div className="flex items-center justify-between mb-2">
                <h2 className="font-display text-lg text-slate-800">Ancrage Bitcoin OpenTimestamps</h2>
                <span data-testid="proof-ots-status" className={`px-2.5 py-1 rounded-full font-mono text-[10px] uppercase tracking-wider border ${
                  otsStatus?.confirmed ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
                  : otsStatus?.upgraded ? 'bg-amber-50 border-amber-200 text-amber-700'
                  : 'bg-slate-50 border-slate-200 text-slate-500'
                }`}>
                  {otsStatus?.confirmed ? 'Confirmé Bitcoin' : otsStatus?.upgraded ? 'Upgraded (en attente confirmation)' : 'Pending (submitted)'}
                </span>
              </div>
              {otsStatus?.btc_block_height && (
                <div className="font-mono text-xs text-slate-600 mt-2">
                  Bloc Bitcoin <span className="text-[#f7931a] font-semibold">#{otsStatus.btc_block_height}</span>
                  {otsStatus.btc_attestations && ` · ${otsStatus.btc_attestations} attestations`}
                </div>
              )}
              {!otsStatus && (
                <p className="font-mono text-[11px] text-slate-400 mt-1">
                  Le statut OTS est rafraîchi périodiquement (calendar.opentimestamps.org).
                </p>
              )}
            </section>

            {/* GEO ANCHOR — temoin satellite */}
            {isGeoAnchor && geo && (
              <section data-testid="proof-geo" className="bg-white/70 backdrop-blur-2xl border border-white/60 rounded-2xl p-5 sm:p-6 shadow-md mb-6">
                <h2 className="font-display text-lg text-slate-800 mb-4">Témoin spatial indépendant</h2>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
                  <div>
                    <div className="font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest">Plus Code (lisible)</div>
                    <div data-testid="proof-plus-code" className="font-display text-xl text-slate-800 tabular-nums mt-1">{geo.plus_code}</div>
                    <div className="font-mono text-[10px] text-slate-400 mt-1">HD : {geo.plus_code_hd}</div>
                  </div>
                  <div>
                    <div className="font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest">Coordonnées</div>
                    <div className="font-mono text-sm text-slate-800 mt-1 tabular-nums">{geo.lat}, {geo.lon}</div>
                    <div className="font-mono text-[10px] text-slate-400 mt-1">H3-9 : {geo.h3_9}</div>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {eoxImg && (
                    <div>
                      <div className="font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest mb-1">Sentinel-2 (10m)</div>
                      <img data-testid="proof-sat-eox" src={eoxImg} alt="Sentinel-2 satellite tile" className="w-full aspect-square object-cover rounded-xl border border-slate-200" loading="lazy" />
                    </div>
                  )}
                  {gibsImg && (
                    <div>
                      <div className="font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest mb-1">NASA GIBS · {satWitness?.nasa_gibs?.date}</div>
                      <img data-testid="proof-sat-gibs" src={gibsImg} alt="NASA GIBS satellite tile" className="w-full aspect-square object-cover rounded-xl border border-slate-200" loading="lazy" />
                    </div>
                  )}
                </div>
                <p className="font-mono text-[10px] text-slate-400 mt-3 leading-relaxed">
                  La paire (Plus Code, tuile satellite à date connue) constitue un témoin spatial indépendant : 
                  un tiers peut vérifier qu'à cette date l'image satellite réelle correspond à cette zone.
                </p>
              </section>
            )}

            {/* QR partageable */}
            <section data-testid="proof-share" className="bg-white/70 backdrop-blur-2xl border border-white/60 rounded-2xl p-5 sm:p-6 shadow-md flex flex-wrap items-center justify-between gap-4">
              <div className="flex-1 min-w-0">
                <h2 className="font-display text-lg text-slate-800 mb-1">Partager cette preuve</h2>
                <p className="font-mono text-[11px] text-slate-500">
                  Lien public — vérifiable par tout journaliste, institution ou partenaire.
                </p>
                <code className="font-mono text-[10px] text-slate-700 break-all block mt-2">{proofUrl}</code>
                <CopyButton value={proofUrl} testid="proof-copy-url" />
              </div>
              <div className="shrink-0 rounded-xl bg-white p-2 border border-slate-200">
                <QRCodeSVG data-testid="proof-qr" value={proofUrl} size={96} level="M" fgColor="#0ea5e9" />
              </div>
            </section>

            <div className="text-center mt-8">
              <Link to="/explorer" data-testid="proof-link-explorer" className="font-mono text-xs text-slate-500 hover:text-[#0ea5e9] uppercase tracking-widest transition">
                ← Explorer la FREK-Chain
              </Link>
            </div>
          </>
        )}
      </main>

      <footer className="relative z-10 border-t border-slate-200/70 mt-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6 flex flex-wrap items-center justify-between gap-3 font-mono text-[10px] text-slate-400 uppercase tracking-widest">
          <span>Preuve souveraine · vérifiable à perpétuité</span>
          <Link to="/atlas" className="hover:text-[#0ea5e9]">Atlas</Link>
        </div>
      </footer>
    </div>
  );
}
