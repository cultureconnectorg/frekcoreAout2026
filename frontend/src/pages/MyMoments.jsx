import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';

const API = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;
const SESSION_KEY = 'frek_moment_session';

/**
 * FREKCORE — Ton univers de moments.
 *
 * Affiche tous les moments signes depuis cette session anonyme,
 * puis propose l'association d'identite (email/passkey) pour les conserver
 * sur tous les appareils.
 */
export default function MyMoments() {
  const [moments, setMoments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sessionId, setSessionId] = useState('');

  useEffect(() => {
    const s = localStorage.getItem(SESSION_KEY);
    if (!s) {
      setLoading(false);
      return;
    }
    setSessionId(s);
    axios.get(`${API}/api/v1/moment/mine?session_id=${s}`)
      .then(({ data }) => {
        setMoments(data.moments || []);
      })
      .catch(() => setMoments([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-white via-blue-50 to-blue-100">
      <header className="p-6 flex justify-between items-center max-w-5xl mx-auto">
        <Link to="/" className="text-xl font-bold text-slate-900" data-testid="mine-brand">
          FREKCORE
        </Link>
        <nav className="flex gap-4 text-sm text-slate-600">
          <Link to="/" className="hover:text-blue-600" data-testid="link-back-sign">← Signer</Link>
          <Link to="/spec" className="hover:text-blue-600" data-testid="link-spec-mine">Spec</Link>
        </nav>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-12">
        <h1 className="text-5xl font-black tracking-tighter text-slate-900 mb-2" data-testid="mine-headline">
          Ton univers.
        </h1>
        <p className="text-slate-600 mb-8">
          {moments.length === 0
            ? 'Aucun moment signé pour l\'instant.'
            : `${moments.length} moment${moments.length > 1 ? 's' : ''} signé${moments.length > 1 ? 's' : ''} depuis ce navigateur.`}
        </p>

        {moments.length >= 3 && (
          <div className="bg-blue-50 border border-blue-200 rounded-2xl p-6 mb-8" data-testid="mine-attach-prompt">
            <div className="text-lg font-bold text-slate-900 mb-2">Conserver ton univers ?</div>
            <p className="text-sm text-slate-600 mb-4">
              Associe une identité pour retrouver tes moments sur tous tes appareils. Aucune donnée n'est publiée — seul un hash est stocké.
            </p>
            <button
              disabled
              className="px-5 py-2 bg-slate-300 text-slate-600 rounded-full text-sm cursor-not-allowed"
              data-testid="mine-attach-btn"
            >
              Associer un email (bientôt)
            </button>
          </div>
        )}

        {loading ? (
          <div className="text-center py-12 text-slate-500" data-testid="mine-loading">Chargement…</div>
        ) : moments.length === 0 ? (
          <div className="text-center py-12">
            <Link
              to="/"
              className="inline-block px-8 py-4 bg-slate-900 text-white rounded-full font-bold hover:bg-slate-700 transition"
              data-testid="mine-cta-first"
            >
              Signer ton premier moment
            </Link>
          </div>
        ) : (
          <div className="space-y-3" data-testid="mine-list">
            {moments.map((m) => (
              <Link
                to={`/verify/${m.frek_id}`}
                key={m.frek_id}
                className="block bg-white/70 backdrop-blur border border-slate-200 rounded-xl p-5 hover:border-blue-400 hover:shadow-md transition"
                data-testid={`mine-item-${m.frek_id}`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="text-slate-900 font-semibold truncate">
                      {m.metadata?.title || 'Moment sans titre'}
                    </div>
                    <div className="text-xs text-slate-500 font-mono mt-1 truncate">#{m.frek_id}</div>
                    <div className="text-xs text-slate-400 mt-2">
                      {new Date(m.created_at).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' })}
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-1 justify-end">
                    {(m.metadata?.layers_captured || []).map((l) => (
                      <span key={l} className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full text-[10px]">{l}</span>
                    ))}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </main>

      <footer className="p-6 text-center text-xs text-slate-400">
        Session anonyme : <span className="font-mono">{sessionId.slice(0, 8)}…</span>
      </footer>
    </div>
  );
}
