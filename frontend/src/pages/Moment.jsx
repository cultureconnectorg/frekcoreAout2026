import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';

/**
 * FREKCORE — Fenetre d'acces #1 : Signer le moment present.
 *
 * Un seul geste. Une preuve immediate. Aucune inscription.
 * L'utilisateur decouvre progressivement la profondeur de l'infrastructure.
 */

const API = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;

const SESSION_KEY = 'frek_moment_session';
const MOMENTS_KEY = 'frek_moments_local';

function getSession() {
  let s = localStorage.getItem(SESSION_KEY);
  if (!s) {
    s = crypto.randomUUID();
    localStorage.setItem(SESSION_KEY, s);
  }
  return s;
}

function getLocalMoments() {
  try {
    return JSON.parse(localStorage.getItem(MOMENTS_KEY) || '[]');
  } catch {
    return [];
  }
}

function saveLocalMoment(m) {
  const list = getLocalMoments();
  list.unshift(m);
  localStorage.setItem(MOMENTS_KEY, JSON.stringify(list.slice(0, 100)));
}

export default function Moment() {
  const [phase, setPhase] = useState('idle'); // idle | signing | done | error
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [localMoments, setLocalMoments] = useState(getLocalMoments());
  const [showTitleInput, setShowTitleInput] = useState(false);
  const [title, setTitle] = useState('');
  const [geoConsent, setGeoConsent] = useState(false);

  useEffect(() => {
    // Genere une session si absente
    getSession();
  }, []);

  const captureGeo = () => {
    return new Promise((resolve) => {
      if (!navigator.geolocation || !geoConsent) {
        resolve(null);
        return;
      }
      navigator.geolocation.getCurrentPosition(
        (pos) => resolve({
          lat: Math.round(pos.coords.latitude * 10000) / 10000,
          lon: Math.round(pos.coords.longitude * 10000) / 10000,
          accuracy_m: Math.round(pos.coords.accuracy),
        }),
        () => resolve(null),
        { timeout: 3000, maximumAge: 60000 }
      );
    });
  };

  const sign = async () => {
    setPhase('signing');
    setError('');

    const geo = await captureGeo();
    const session_id = getSession();

    try {
      const { data } = await axios.post(`${API}/api/v1/moment/sign`, {
        title: title.trim() || null,
        geo,
        session_id,
      });
      setResult(data);
      saveLocalMoment(data);
      setLocalMoments(getLocalMoments());
      setPhase('done');
    } catch (e) {
      setError(e.response?.data?.detail || 'Erreur reseau. Reessaye.');
      setPhase('error');
    }
  };

  const reset = () => {
    setPhase('idle');
    setResult(null);
    setTitle('');
    setShowTitleInput(false);
    setError('');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-white via-blue-50 to-blue-100 flex flex-col">
      {/* Header minimal */}
      <header className="p-6 flex justify-between items-center">
        <div className="text-xl font-bold tracking-tight text-slate-900" data-testid="moment-brand">
          FREKCORE
        </div>
        <nav className="flex gap-4 text-sm text-slate-600">
          <Link to="/certify" className="hover:text-blue-600 transition" data-testid="link-manifesto">Manifeste</Link>
          <Link to="/spec" className="hover:text-blue-600 transition" data-testid="link-spec">Spec</Link>
          <Link to="/explorer" className="hover:text-blue-600 transition" data-testid="link-explorer">Explorer</Link>
        </nav>
      </header>

      {/* Main gesture */}
      <main className="flex-1 flex flex-col items-center justify-center px-6 py-12">
        {phase === 'idle' && (
          <div className="text-center max-w-xl">
            <h1 className="text-6xl md:text-7xl font-black tracking-tighter text-slate-900 mb-4" data-testid="moment-headline">
              Signe ce moment.
            </h1>
            <p className="text-base md:text-lg text-slate-600 mb-12 font-light">
              Un geste. Une preuve. Notariée sur Bitcoin. Vérifiable à vie.
            </p>

            <button
              onClick={sign}
              className="group relative px-16 py-8 bg-slate-900 text-white text-2xl font-bold rounded-full shadow-2xl hover:shadow-3xl hover:scale-105 active:scale-95 transition-all duration-200 tracking-wider"
              data-testid="moment-sign-btn"
            >
              SIGNER
              <span className="absolute -inset-1 rounded-full bg-blue-400 opacity-0 group-hover:opacity-20 blur transition"></span>
            </button>

            {/* Options discretes */}
            <div className="mt-10 flex flex-col items-center gap-3 text-sm text-slate-500">
              {!showTitleInput ? (
                <button
                  onClick={() => setShowTitleInput(true)}
                  className="text-slate-500 hover:text-slate-900 underline underline-offset-4"
                  data-testid="moment-add-title"
                >
                  + Ajouter un titre (optionnel)
                </button>
              ) : (
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Ex : coucher de soleil, concert, réunion..."
                  className="px-4 py-2 border border-slate-300 rounded-lg text-slate-900 w-72 focus:outline-none focus:border-blue-500"
                  maxLength={200}
                  data-testid="moment-title-input"
                />
              )}

              <label className="flex items-center gap-2 cursor-pointer" data-testid="moment-geo-toggle">
                <input
                  type="checkbox"
                  checked={geoConsent}
                  onChange={(e) => setGeoConsent(e.target.checked)}
                  className="w-4 h-4"
                />
                <span>Autoriser la localisation (H3, précision 10m)</span>
              </label>
            </div>

            {localMoments.length > 0 && (
              <div className="mt-16 text-sm text-slate-500" data-testid="moment-history-hint">
                Tu as déjà signé {localMoments.length} moment{localMoments.length > 1 ? 's' : ''} depuis ce navigateur.{' '}
                <Link to="/mine" className="text-blue-600 hover:underline" data-testid="link-mine">
                  Voir ton univers →
                </Link>
              </div>
            )}
          </div>
        )}

        {phase === 'signing' && (
          <div className="text-center" data-testid="moment-signing">
            <div className="w-16 h-16 border-4 border-slate-900 border-t-transparent rounded-full animate-spin mx-auto mb-6"></div>
            <p className="text-lg text-slate-700">Signature en cours…</p>
            <p className="text-sm text-slate-500 mt-2">Notarisation Bitcoin • Signature Ed25519</p>
          </div>
        )}

        {phase === 'done' && result && (
          <div className="text-center max-w-2xl" data-testid="moment-done">
            <div className="text-6xl mb-4">✓</div>
            <h2 className="text-3xl font-bold text-slate-900 mb-2">
              Ton moment est signé.
            </h2>
            <p className="text-sm text-slate-500 mb-8">
              #{result.frek_id}
            </p>

            <div className="bg-white/70 backdrop-blur border border-slate-200 rounded-2xl p-8 text-left space-y-4 mb-8">
              <div>
                <div className="text-xs text-slate-400 uppercase tracking-wider">Signé à</div>
                <div className="text-slate-900 font-mono text-sm">
                  {new Date(result.created_at).toLocaleString('fr-FR', { dateStyle: 'full', timeStyle: 'medium' })}
                </div>
              </div>
              <div>
                <div className="text-xs text-slate-400 uppercase tracking-wider">Block FREK-Chain</div>
                <div className="text-slate-900 font-mono text-xs break-all">
                  {result.block_hash || 'En cours de notarisation…'}
                </div>
              </div>
              <div>
                <div className="text-xs text-slate-400 uppercase tracking-wider">Couches capturées</div>
                <div className="flex flex-wrap gap-2 mt-1">
                  {result.layers_captured.map((l) => (
                    <span key={l} className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-xs">
                      {l}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex flex-wrap justify-center gap-3">
              <Link
                to={`/verify/${result.frek_id}`}
                className="px-6 py-3 bg-slate-900 text-white rounded-full font-semibold hover:bg-slate-700 transition"
                data-testid="moment-see-proof"
              >
                Voir la preuve
              </Link>
              {result.block_hash && (
                <Link
                  to={result.proof_url}
                  className="px-6 py-3 bg-white border border-slate-300 text-slate-900 rounded-full font-semibold hover:bg-slate-50 transition"
                  data-testid="moment-see-block"
                >
                  Explorer le block
                </Link>
              )}
              <button
                onClick={reset}
                className="px-6 py-3 bg-blue-600 text-white rounded-full font-semibold hover:bg-blue-700 transition"
                data-testid="moment-sign-another"
              >
                Signer un autre moment
              </button>
            </div>

            <p className="text-xs text-slate-400 mt-8" data-testid="moment-anonymous-notice">
              Ce moment est anonyme. Il vit dans ce navigateur.
              <br />
              Pour le conserver sur tous tes appareils, associe une identité plus tard.
            </p>
          </div>
        )}

        {phase === 'error' && (
          <div className="text-center max-w-md" data-testid="moment-error">
            <div className="text-4xl mb-4">⚠</div>
            <p className="text-slate-900 font-semibold mb-2">{error}</p>
            <button
              onClick={reset}
              className="mt-4 px-6 py-3 bg-slate-900 text-white rounded-full font-semibold hover:bg-slate-700"
              data-testid="moment-retry"
            >
              Réessayer
            </button>
          </div>
        )}
      </main>

      <footer className="p-6 text-center text-xs text-slate-400">
        FREKCORE — Infrastructure de preuve culturelle • <Link to="/spec" className="hover:text-slate-600">v1.0</Link>
      </footer>
    </div>
  );
}
