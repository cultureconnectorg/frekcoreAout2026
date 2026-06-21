/**
 * FREK — Block Explorer Public /explorer
 *
 * Liste paginée de la FREK-Chain. Cliquer un bloc → /proof/:hash.
 * Lecture seule via `GET /api/v1/notary/blocks` + `GET /api/v1/notary/chain/status`.
 */
import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

const API_URL = import.meta.env.VITE_BACKEND_URL || '';
const PAGE_SIZE = 25;

function BackgroundDecor() {
  return (
    <>
      <div aria-hidden className="absolute -top-32 -right-32 w-[500px] h-[500px] bg-gradient-to-br from-[#2cc4f5] to-[#06b6d4] rounded-full blur-3xl opacity-30" />
      <div aria-hidden className="absolute -bottom-40 -left-40 w-[600px] h-[600px] bg-gradient-to-tr from-[#0ea5e9] to-[#2cc4f5] rounded-full blur-3xl opacity-25" />
    </>
  );
}

const TYPE_BADGES = {
  identity_emit: { color: 'bg-blue-50 text-blue-700 border-blue-200', label: 'Identité' },
  stage_transition: { color: 'bg-cyan-50 text-cyan-700 border-cyan-200', label: 'Stage' },
  badge_emit: { color: 'bg-purple-50 text-purple-700 border-purple-200', label: 'Badge' },
  geo_anchor: { color: 'bg-emerald-50 text-emerald-700 border-emerald-200', label: 'Geo' },
  scan_access: { color: 'bg-amber-50 text-amber-700 border-amber-200', label: 'Scan' },
};

export default function Explorer() {
  const [blocks, setBlocks] = useState([]);
  const [status, setStatus] = useState(null);
  const [page, setPage] = useState(0);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true); setError(null);
      try {
        const [bRes, sRes] = await Promise.allSettled([
          fetch(`${API_URL}/api/v1/notary/blocks?limit=500`),
          fetch(`${API_URL}/api/v1/notary/chain/status`),
        ]);
        if (cancelled) return;
        if (bRes.status === 'fulfilled' && bRes.value.ok) setBlocks(await bRes.value.json());
        if (sRes.status === 'fulfilled' && sRes.value.ok) setStatus(await sRes.value.json());
      } catch {
        if (!cancelled) setError('Chain injoignable');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    const id = setInterval(load, 30_000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  const filtered = useMemo(() => {
    if (!search.trim()) return blocks;
    const q = search.trim().toLowerCase();
    return blocks.filter((b) =>
      b.block_hash?.toLowerCase().includes(q) ||
      b.payload_id?.toLowerCase().includes(q) ||
      b.payload_type?.toLowerCase().includes(q) ||
      String(b.height).includes(q),
    );
  }, [blocks, search]);

  const pageItems = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-800 relative overflow-hidden">
      <BackgroundDecor />

      <header className="relative z-10 max-w-6xl mx-auto px-4 sm:px-6 pt-6">
        <div className="bg-white/70 backdrop-blur-2xl rounded-2xl border border-white/60 shadow-lg shadow-slate-200/50 px-4 sm:px-6 h-14 sm:h-16 flex items-center justify-between">
          <Link to="/accueil" data-testid="explorer-home-link" className="flex items-center gap-2">
            <span className="font-display text-xl tracking-wider bg-gradient-to-r from-[#2cc4f5] to-[#0ea5e9] bg-clip-text text-transparent font-semibold">FREK</span>
          </Link>
          <span className="font-mono text-[10px] text-slate-400 uppercase tracking-widest">FREK-Chain Explorer</span>
        </div>
      </header>

      <main className="relative z-10 max-w-6xl mx-auto px-4 sm:px-6 py-10 sm:py-14">
        <div className="mb-8">
          <div className="font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest mb-2">Transparence radicale</div>
          <h1 data-testid="explorer-title" className="font-display text-4xl sm:text-5xl text-slate-800">FREK-Chain</h1>
          <p className="font-mono text-sm text-slate-500 mt-3 max-w-2xl">
            Chaîne souveraine ancrée sur Bitcoin via OpenTimestamps. Chaque ligne est une preuve
            vérifiable à perpétuité.
          </p>
        </div>

        {/* Status chain */}
        <section data-testid="explorer-status" className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
          <div className="bg-white/70 backdrop-blur-xl border border-white/60 rounded-xl p-4 shadow-sm">
            <div className="font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest">Hauteur</div>
            <div data-testid="explorer-height" className="font-display text-2xl text-slate-800 tabular-nums mt-1">{status?.height ?? '—'}</div>
          </div>
          <div className="bg-white/70 backdrop-blur-xl border border-white/60 rounded-xl p-4 shadow-sm">
            <div className="font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest">Blocks visibles</div>
            <div className="font-display text-2xl text-slate-800 tabular-nums mt-1">{blocks.length}</div>
          </div>
          <div className="bg-white/70 backdrop-blur-xl border border-white/60 rounded-xl p-4 shadow-sm">
            <div className="font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest">Pending OTS</div>
            <div className="font-display text-2xl text-slate-800 tabular-nums mt-1">{status?.pending_ots ?? '—'}</div>
          </div>
          <div className="bg-white/70 backdrop-blur-xl border border-white/60 rounded-xl p-4 shadow-sm">
            <div className="font-mono text-[10px] text-[#0ea5e9] uppercase tracking-widest">Genesis</div>
            <div className="font-mono text-[11px] text-slate-700 mt-1">{status?.genesis_at ? new Date(status.genesis_at).toLocaleDateString('fr-FR') : '—'}</div>
          </div>
        </section>

        {/* Recherche */}
        <section className="mb-6">
          <input
            type="text"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(0); }}
            placeholder="Rechercher par hash, payload_id, type, hauteur..."
            data-testid="explorer-search"
            className="w-full bg-white border border-slate-200 focus:border-[#2cc4f5] focus:ring-2 focus:ring-[#2cc4f5]/20 outline-none rounded-xl px-4 py-3 font-mono text-sm text-slate-700 placeholder:text-slate-300 shadow-sm"
          />
        </section>

        {error && (
          <div className="rounded-lg p-3 bg-red-50 border border-red-200 font-mono text-[11px] text-red-600 mb-6">{error}</div>
        )}

        {/* Table blocks */}
        <section data-testid="explorer-blocks" className="bg-white/70 backdrop-blur-2xl border border-white/60 rounded-2xl shadow-lg shadow-slate-200/40 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50/80 border-b border-slate-200">
                <tr>
                  <th className="font-mono text-[10px] text-slate-500 uppercase tracking-widest text-left px-4 py-3">#</th>
                  <th className="font-mono text-[10px] text-slate-500 uppercase tracking-widest text-left px-4 py-3">Type</th>
                  <th className="font-mono text-[10px] text-slate-500 uppercase tracking-widest text-left px-4 py-3 hidden sm:table-cell">Payload</th>
                  <th className="font-mono text-[10px] text-slate-500 uppercase tracking-widest text-left px-4 py-3 hidden md:table-cell">Hash</th>
                  <th className="font-mono text-[10px] text-slate-500 uppercase tracking-widest text-right px-4 py-3">Quand</th>
                </tr>
              </thead>
              <tbody>
                {loading && (
                  <tr><td colSpan="5" className="text-center py-10 font-mono text-xs text-slate-400">Chargement…</td></tr>
                )}
                {!loading && pageItems.length === 0 && (
                  <tr><td colSpan="5" className="text-center py-10 font-mono text-xs text-slate-400" data-testid="explorer-empty">Aucun bloc trouvé.</td></tr>
                )}
                {pageItems.map((b) => {
                  const t = TYPE_BADGES[b.payload_type] || { color: 'bg-slate-50 text-slate-600 border-slate-200', label: b.payload_type };
                  return (
                    <tr key={b.height} className="border-b border-slate-100 hover:bg-slate-50/50 transition">
                      <td className="px-4 py-3">
                        <Link to={`/proof/${encodeURIComponent(b.block_hash)}`} data-testid={`explorer-row-${b.height}`} className="font-display text-sm text-slate-800 hover:text-[#0ea5e9] tabular-nums">
                          #{b.height}
                        </Link>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-block px-2 py-0.5 rounded-full border font-mono text-[10px] uppercase tracking-wider ${t.color}`}>{t.label}</span>
                      </td>
                      <td className="px-4 py-3 hidden sm:table-cell">
                        <code className="font-mono text-[11px] text-slate-600 truncate block max-w-[200px]">{b.payload_id}</code>
                      </td>
                      <td className="px-4 py-3 hidden md:table-cell">
                        <code className="font-mono text-[10px] text-slate-500 truncate block max-w-[140px]">{b.block_hash}</code>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <span className="font-mono text-[10px] text-slate-400">{new Date(b.timestamp).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}</span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between gap-3 px-4 py-3 border-t border-slate-100">
              <span className="font-mono text-[10px] text-slate-400 uppercase tracking-widest">
                Page {page + 1} / {totalPages} · {filtered.length} blocs
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  disabled={page === 0}
                  data-testid="explorer-prev"
                  className="px-3 py-1.5 bg-white border border-slate-200 hover:border-[#2cc4f5] disabled:opacity-30 disabled:cursor-not-allowed font-mono text-[10px] uppercase tracking-wider text-slate-600 rounded-lg transition"
                >
                  Précédent
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                  disabled={page >= totalPages - 1}
                  data-testid="explorer-next"
                  className="px-3 py-1.5 bg-white border border-slate-200 hover:border-[#2cc4f5] disabled:opacity-30 disabled:cursor-not-allowed font-mono text-[10px] uppercase tracking-wider text-slate-600 rounded-lg transition"
                >
                  Suivant
                </button>
              </div>
            </div>
          )}
        </section>
      </main>

      <footer className="relative z-10 border-t border-slate-200/70 mt-16">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6 flex flex-wrap items-center justify-between gap-3 font-mono text-[10px] text-slate-400 uppercase tracking-widest">
          <span>FREK-Chain · ancrage Bitcoin OTS</span>
          <div className="flex gap-4">
            <Link to="/atlas" className="hover:text-[#0ea5e9]">Atlas</Link>
            <Link to="/accueil" className="hover:text-[#0ea5e9]">Accueil</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
