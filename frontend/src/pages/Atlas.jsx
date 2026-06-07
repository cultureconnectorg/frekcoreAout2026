/**
 * FREK — Atlas /atlas
 * Visualisation reelle du Geo Layer souverain :
 *  - Heatmap anonyme par cellule H3 (consomme /api/geo/heatmap)
 *  - Image satellite Sentinel-2 reelle de la cellule la plus active
 *  - Image NASA GIBS quotidienne
 *  - Compteurs par pays
 *
 * Theme clair Certify-style. Aucune PII exposee.
 */
import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

const API_URL = import.meta.env.VITE_BACKEND_URL || '';

// Coordonnees representatives par H3 cell — pour v1 on utilise une projection inverse approximative
// via le bbox H3 calcule cote backend. Pour la demo on demande au backend les URLs satellite
// d'un point connu (Fort-de-France = barycentre CC2026).
const FORT_DE_FRANCE = { lat: 14.6037, lon: -61.0594 };
const PARIS = { lat: 48.8566, lon: 2.3522 };
const TOKYO = { lat: 35.6762, lon: 139.6503 };

const COUNTRY_NAMES = {
  FR: 'France', US: 'États-Unis', JP: 'Japon', BR: 'Brésil', SN: 'Sénégal',
  CI: "Côte d'Ivoire", MA: 'Maroc', CA: 'Canada', BE: 'Belgique', CH: 'Suisse',
  HT: 'Haïti', DO: 'République Dominicaine', GB: 'Royaume-Uni', DE: 'Allemagne',
};

function flagEmoji(cc) {
  if (!cc || cc.length !== 2) return '🌐';
  const A = 0x1F1E6;
  return String.fromCodePoint(...cc.toUpperCase().split('').map((c) => A + c.charCodeAt(0) - 65));
}

function BackgroundDecor() {
  return (
    <>
      <div aria-hidden className="absolute -top-32 -right-32 w-[500px] h-[500px] bg-gradient-to-br from-[#2cc4f5] to-[#06b6d4] rounded-full blur-3xl opacity-30" />
      <div aria-hidden className="absolute -bottom-40 -left-40 w-[600px] h-[600px] bg-gradient-to-tr from-[#0ea5e9] to-[#2cc4f5] rounded-full blur-3xl opacity-25" />
    </>
  );
}

export default function Atlas() {
  const [heatmap, setHeatmap] = useState(null);
  const [sources, setSources] = useState(null);
  const [satEox, setSatEox] = useState(null);
  const [satGibs, setSatGibs] = useState(null);
  const [satPoint, setSatPoint] = useState(FORT_DE_FRANCE);
  const [zoom, setZoom] = useState(12);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const [hRes, sRes] = await Promise.allSettled([
          fetch(`${API_URL}/api/geo/heatmap`),
          fetch(`${API_URL}/api/geo/satellite/sources`),
        ]);
        if (cancelled) return;
        if (hRes.status === 'fulfilled' && hRes.value.ok) setHeatmap(await hRes.value.json());
        if (sRes.status === 'fulfilled' && sRes.value.ok) setSources(await sRes.value.json());
      } catch { if (!cancelled) setError('Backend injoignable'); }
    };
    load();
    const id = setInterval(load, 30_000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const z = Math.min(Math.max(zoom, 0), 18);
        const eoxUrl = `${API_URL}/api/geo/satellite?lat=${satPoint.lat}&lon=${satPoint.lon}&provider=eox_s2&zoom=${z}`;
        const gibsUrl = `${API_URL}/api/geo/satellite?lat=${satPoint.lat}&lon=${satPoint.lon}&provider=gibs&zoom=${Math.min(z, 9)}`;
        const [eRes, gRes] = await Promise.allSettled([fetch(eoxUrl), fetch(gibsUrl)]);
        if (cancelled) return;
        if (eRes.status === 'fulfilled' && eRes.value.ok) setSatEox(await eRes.value.json());
        if (gRes.status === 'fulfilled' && gRes.value.ok) setSatGibs(await gRes.value.json());
      } catch { /* noop */ }
    };
    load();
  }, [satPoint, zoom]);

  const countries = useMemo(() => {
    if (!heatmap?.by_country) return [];
    return Object.entries(heatmap.by_country)
      .map(([cc, n]) => ({ cc, n, name: COUNTRY_NAMES[cc] || cc }))
      .sort((a, b) => b.n - a.n);
  }, [heatmap]);

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-800 relative overflow-hidden">
      <BackgroundDecor />

      <header className="relative z-10 max-w-6xl mx-auto px-4 sm:px-6 pt-6">
        <div className="bg-white/70 backdrop-blur-2xl rounded-2xl border border-white/60 shadow-lg shadow-slate-200/50 px-4 sm:px-6 h-14 sm:h-16 flex items-center justify-between">
          <Link to="/accueil" data-testid="atlas-home-link" className="flex items-center gap-2">
            <span className="font-display text-xl tracking-wider bg-gradient-to-r from-[#2cc4f5] to-[#0ea5e9] bg-clip-text text-transparent font-semibold">FREK</span>
          </Link>
          <span className="font-mono text-[10px] text-slate-400 uppercase tracking-widest">Atlas mondial</span>
        </div>
      </header>

      <main className="relative z-10 max-w-6xl mx-auto px-4 sm:px-6 py-10 sm:py-14">
        <div className="mb-10">
          <div className="font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest mb-2">Geolocalite souveraine — Phase 6</div>
          <h1 data-testid="atlas-title" className="font-display text-4xl sm:text-5xl text-slate-800">Atlas FrekCore</h1>
          <p className="font-mono text-sm text-slate-500 mt-3 max-w-2xl">
            Carte chaude mondiale des présences certifiées. Cellules H3 (~175m), agrégation anonyme,
            imagerie satellite gratuite (NASA GIBS + Sentinel-2 EOX). Aucun secret, aucune dépendance commerciale.
          </p>
        </div>

        {error && (
          <div className="rounded-lg p-3 bg-red-50 border border-red-200 font-mono text-[11px] text-red-600 mb-6" data-testid="atlas-error">{error}</div>
        )}

        {/* Compteurs globaux */}
        <section className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
          <div className="bg-white/70 backdrop-blur-xl border border-white/60 rounded-xl p-5 shadow-md">
            <div className="font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest">Cellules actives</div>
            <div data-testid="atlas-total-cells" className="font-display text-3xl text-slate-800 tabular-nums mt-1">
              {heatmap?.total_cells?.toLocaleString('fr-FR') ?? '—'}
            </div>
            <div className="font-mono text-[10px] text-slate-400 mt-1">H3 résolution 9 (~175m)</div>
          </div>
          <div className="bg-white/70 backdrop-blur-xl border border-white/60 rounded-xl p-5 shadow-md">
            <div className="font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest">Pays couverts</div>
            <div data-testid="atlas-total-countries" className="font-display text-3xl text-slate-800 tabular-nums mt-1">
              {countries.length || '—'}
            </div>
            <div className="font-mono text-[10px] text-slate-400 mt-1">via Nominatim OSM (gratuit)</div>
          </div>
          <div className="bg-white/70 backdrop-blur-xl border border-white/60 rounded-xl p-5 shadow-md">
            <div className="font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest">Observations 24h</div>
            <div data-testid="atlas-obs-24h" className="font-display text-3xl text-slate-800 tabular-nums mt-1">
              {heatmap?.observations_last_24h?.toLocaleString('fr-FR') ?? '—'}
            </div>
            <div className="font-mono text-[10px] text-slate-400 mt-1">opt-in segmenté · purge sur révocation</div>
          </div>
        </section>

        {/* Pays */}
        <section data-testid="atlas-countries" className="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl p-5 sm:p-6 shadow-md mb-10">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-display text-xl text-slate-800">Présences par pays</h2>
            <span className="font-mono text-[10px] text-slate-400 uppercase tracking-widest">classement live</span>
          </div>
          {countries.length === 0 ? (
            <p className="font-mono text-sm text-slate-400 italic">Aucune observation enregistrée pour l'instant. Active le partage de position dans <Link to="/scanner" className="text-[#0ea5e9] underline">le scanner</Link>.</p>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {countries.map((c) => (
                <div key={c.cc} className="flex items-center gap-3 bg-white border border-slate-100 rounded-lg px-3 py-2">
                  <span className="text-xl">{flagEmoji(c.cc)}</span>
                  <div className="flex-1 min-w-0">
                    <div className="font-mono text-sm text-slate-800 truncate">{c.name}</div>
                    <div className="font-mono text-[10px] text-slate-400 tabular-nums">{c.n} obs.</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Cellules H3 top */}
        <section data-testid="atlas-cells" className="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl p-5 sm:p-6 shadow-md mb-10">
          <h2 className="font-display text-xl text-slate-800 mb-4">Cellules H3 les plus actives</h2>
          {(heatmap?.cells || []).slice(0, 12).map((cell, i) => (
            <div key={cell.h3_9} className="flex items-center justify-between gap-3 py-2 border-b border-slate-100 last:border-0">
              <div className="flex items-center gap-3 min-w-0">
                <span className="text-lg">{flagEmoji(cell.country_code)}</span>
                <code className="font-mono text-xs text-slate-600 truncate">{cell.h3_9}</code>
              </div>
              <div className="font-mono text-sm text-slate-800 tabular-nums shrink-0">{cell.count}</div>
            </div>
          ))}
          {(!heatmap?.cells || heatmap.cells.length === 0) && (
            <p className="font-mono text-sm text-slate-400 italic">Aucune cellule active pour l'instant.</p>
          )}
        </section>

        {/* Imagerie satellite reelle */}
        <section data-testid="atlas-satellite" className="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl p-5 sm:p-6 shadow-md mb-10">
          <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
            <h2 className="font-display text-xl text-slate-800">Imagerie satellite gratuite</h2>
            <div className="flex gap-2">
              <button onClick={() => setSatPoint(FORT_DE_FRANCE)} data-testid="atlas-sat-fdf" className={`px-3 py-1.5 rounded-lg font-mono text-[10px] uppercase tracking-wider transition ${JSON.stringify(satPoint)===JSON.stringify(FORT_DE_FRANCE)?'bg-gradient-to-r from-[#2cc4f5] to-[#0ea5e9] text-white':'bg-white border border-slate-200 text-slate-600 hover:border-[#2cc4f5]'}`}>Fort-de-France</button>
              <button onClick={() => setSatPoint(PARIS)} data-testid="atlas-sat-paris" className={`px-3 py-1.5 rounded-lg font-mono text-[10px] uppercase tracking-wider transition ${JSON.stringify(satPoint)===JSON.stringify(PARIS)?'bg-gradient-to-r from-[#2cc4f5] to-[#0ea5e9] text-white':'bg-white border border-slate-200 text-slate-600 hover:border-[#2cc4f5]'}`}>Paris</button>
              <button onClick={() => setSatPoint(TOKYO)} data-testid="atlas-sat-tokyo" className={`px-3 py-1.5 rounded-lg font-mono text-[10px] uppercase tracking-wider transition ${JSON.stringify(satPoint)===JSON.stringify(TOKYO)?'bg-gradient-to-r from-[#2cc4f5] to-[#0ea5e9] text-white':'bg-white border border-slate-200 text-slate-600 hover:border-[#2cc4f5]'}`}>Tokyo</button>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* EOX Sentinel-2 */}
            <div className="space-y-2">
              <div className="font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest">EOX Sentinel-2 cloudless · 10m</div>
              {satEox?.url ? (
                <img
                  data-testid="atlas-sat-eox-img"
                  src={satEox.url}
                  alt="Sentinel-2 satellite tile"
                  className="w-full aspect-square object-cover rounded-xl border border-slate-200 bg-slate-100"
                  loading="lazy"
                />
              ) : (
                <div className="w-full aspect-square rounded-xl border border-slate-200 bg-slate-100 flex items-center justify-center text-slate-400 font-mono text-xs">Chargement…</div>
              )}
              <div className="font-mono text-[10px] text-slate-400 truncate">{satEox?.attribution}</div>
            </div>

            {/* NASA GIBS */}
            <div className="space-y-2">
              <div className="font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest">NASA GIBS · MODIS Terra quotidien</div>
              {satGibs?.url ? (
                <img
                  data-testid="atlas-sat-gibs-img"
                  src={satGibs.url}
                  alt="NASA GIBS satellite tile"
                  className="w-full aspect-square object-cover rounded-xl border border-slate-200 bg-slate-100"
                  loading="lazy"
                />
              ) : (
                <div className="w-full aspect-square rounded-xl border border-slate-200 bg-slate-100 flex items-center justify-center text-slate-400 font-mono text-xs">Chargement…</div>
              )}
              <div className="font-mono text-[10px] text-slate-400 truncate">{satGibs?.attribution} · {satGibs?.date}</div>
            </div>
          </div>
        </section>

        {/* Sources */}
        <section data-testid="atlas-sources" className="bg-white/70 backdrop-blur-xl border border-white/60 rounded-2xl p-5 sm:p-6 shadow-md">
          <h2 className="font-display text-xl text-slate-800 mb-4">Sources câblées</h2>
          {sources?.sources?.map((s) => (
            <div key={s.id} className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0">
              <div>
                <div className="font-mono text-sm text-slate-800">{s.name}</div>
                <div className="font-mono text-[10px] text-slate-400">id: {s.id}{s.resolution_m ? ` · ${s.resolution_m}m` : ''}</div>
              </div>
              <span className="font-mono text-[10px] text-emerald-700 uppercase tracking-widest bg-emerald-50 border border-emerald-200 rounded-full px-2 py-1">
                {s.free ? 'gratuit' : 'payant'} · {s.auth ? 'auth' : 'no-auth'}
              </span>
            </div>
          ))}
          {sources?.geocoding && (
            <div className="flex items-center justify-between py-2 mt-2 pt-3 border-t border-slate-200">
              <div>
                <div className="font-mono text-sm text-slate-800">Nominatim (OSM) — reverse-geocoding</div>
                <div className="font-mono text-[10px] text-slate-400">id: {sources.geocoding.provider} · {sources.geocoding.rate_limit}</div>
              </div>
              <span className="font-mono text-[10px] text-emerald-700 uppercase tracking-widest bg-emerald-50 border border-emerald-200 rounded-full px-2 py-1">
                {sources.geocoding.free ? 'gratuit' : 'payant'} · {sources.geocoding.auth ? 'auth' : 'no-auth'}
              </span>
            </div>
          )}
        </section>
      </main>

      <footer className="relative z-10 border-t border-slate-200/70 mt-16">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6 flex flex-wrap items-center justify-between gap-3 font-mono text-[10px] text-slate-400 uppercase tracking-widest">
          <span>Geo Layer · Plus Code + H3 + Nominatim + NASA GIBS + Sentinel-2 EOX</span>
          <Link to="/scanner" className="hover:text-[#0ea5e9]">Pointeuse →</Link>
        </div>
      </footer>
    </div>
  );
}
