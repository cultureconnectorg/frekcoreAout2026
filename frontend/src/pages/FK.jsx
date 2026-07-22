import { useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import BrandLogo from '../components/BrandLogo';

/**
 * FREKCORE — FK Cultural Object Container (v0.1)
 *
 * Fenetre d'acces publique pour :
 *  - Creer un objet culturel FK (metadata + medias) → export .fk
 *  - Verifier un .fk deja emballe (verification OFFLINE cote client-serveur)
 *
 * Vocabulaire : on n'"emballe pas" — on **exporte un objet culturel FK**.
 */

const API = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;

const OBJECT_TYPES = [
  { value: 'song', label: 'Chanson' },
  { value: 'album', label: 'Album' },
  { value: 'event', label: 'Événement / Festival' },
  { value: 'captation', label: 'Captation live' },
  { value: 'photo', label: 'Photo' },
  { value: 'artwork', label: 'Œuvre' },
  { value: 'heritage', label: 'Patrimoine' },
  { value: 'document', label: 'Document' },
  { value: 'other', label: 'Autre' },
];

export default function FK() {
  const [tab, setTab] = useState('create');
  return (
    <div className="relative min-h-screen bg-gradient-to-br from-white via-blue-50 to-blue-100 flex flex-col overflow-hidden">
      <motion.header
        initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
        className="relative z-10 p-6 flex justify-between items-center max-w-5xl mx-auto w-full"
      >
        <BrandLogo to="/universe" testId="fk-brand" />
        <nav className="flex gap-6 text-sm text-slate-600">
          <Link to="/universe" className="hover:text-blue-600 transition-colors" data-testid="fk-link-universe">Univers</Link>
          <Link to="/" className="hover:text-blue-600 transition-colors" data-testid="fk-link-home">Signer</Link>
          <Link to="/spec" className="hover:text-blue-600 transition-colors" data-testid="fk-link-spec">Charte</Link>
          <Link to="/manifeste" className="hover:text-blue-600 transition-colors" data-testid="fk-link-manifeste">Manifeste</Link>
        </nav>
      </motion.header>

      <main className="relative z-10 flex-1 max-w-3xl mx-auto w-full px-6 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          className="mb-10 text-center"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-blue-50 border border-blue-200 rounded-full text-blue-700 text-xs font-semibold mb-4">
            FK Specification v0.1 · Cultural Object Container
          </div>
          <h1 className="text-4xl md:text-6xl font-black tracking-tighter text-slate-900 mb-3">
            Un objet culturel<br />qui traverse le temps.
          </h1>
          <p className="text-base text-slate-700 max-w-xl mx-auto mb-3 font-medium" data-testid="fk-positioning">
            FK est le format d&apos;objet culturel de FREKCORE : un conteneur qui réunit création, contexte, droits et preuve dans un objet numérique vérifiable.
          </p>
          <p className="text-sm text-slate-500 max-w-xl mx-auto">
            Un fichier <code className="text-blue-700 font-mono">.fk</code> transporte l&apos;identité, l&apos;histoire et la preuve d&apos;une création — pas seulement son contenu.
          </p>
        </motion.div>

        <div className="flex justify-center gap-2 mb-8">
          <button
            onClick={() => setTab('create')}
            className={`px-5 py-2.5 rounded-full text-sm font-semibold transition-all ${
              tab === 'create' ? 'bg-slate-900 text-white shadow-lg' : 'bg-white/60 text-slate-600 hover:bg-white'
            }`}
            data-testid="fk-tab-create"
          >
            Créer un objet FK
          </button>
          <button
            onClick={() => setTab('verify')}
            className={`px-5 py-2.5 rounded-full text-sm font-semibold transition-all ${
              tab === 'verify' ? 'bg-slate-900 text-white shadow-lg' : 'bg-white/60 text-slate-600 hover:bg-white'
            }`}
            data-testid="fk-tab-verify"
          >
            Vérifier un .fk
          </button>
        </div>

        <AnimatePresence mode="wait">
          {tab === 'create' ? <CreateFK key="create" /> : <VerifyFK key="verify" />}
        </AnimatePresence>
      </main>

      <footer className="relative z-10 p-6 text-center text-xs text-slate-400">
        <div className="mb-2 max-w-lg mx-auto leading-relaxed" data-testid="fk-legal-notice">
          FREKCORE atteste l&apos;existence, l&apos;intégrité et l&apos;origine déclarée d&apos;un objet numérique.
        </div>
        FREKCORE — Infrastructure de preuve culturelle • FK v0.1
      </footer>
    </div>
  );
}

// ---------------- CREATE ----------------

function CreateFK() {
  const [form, setForm] = useState({
    title: '',
    object_type: 'song',
    primary_creator_name: '',
    description: '',
    keep: false,
  });
  const [files, setFiles] = useState([]);
  const [phase, setPhase] = useState('idle'); // idle | creating | done | error
  const [result, setResult] = useState(null);
  const [downloadUrl, setDownloadUrl] = useState(null);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  const onFiles = (e) => {
    const selected = Array.from(e.target.files || []);
    setFiles((prev) => [...prev, ...selected]);
  };

  const removeFile = (idx) => {
    setFiles((prev) => prev.filter((_, i) => i !== idx));
  };

  const submit = async () => {
    if (!form.title.trim() || !form.primary_creator_name.trim()) {
      setError('Titre et créateur sont requis.');
      return;
    }
    setPhase('creating');
    setError('');
    try {
      const fd = new FormData();
      fd.append('title', form.title.trim());
      fd.append('object_type', form.object_type);
      fd.append('primary_creator_name', form.primary_creator_name.trim());
      if (form.description.trim()) fd.append('description', form.description.trim());
      fd.append('keep', form.keep ? 'true' : 'false');
      fd.append('return_json', 'true');
      files.forEach((f) => fd.append('files', f));

      const identityToken = localStorage.getItem('frek_identity_token');
      const headers = identityToken ? { 'X-FREK-Session': identityToken } : {};
      const res = await fetch(`${API}/api/v1/fk/create`, { method: 'POST', body: fd, headers });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      const data = await res.json();
      // Decoder le base64 en Blob pour download
      const bin = atob(data.fk_base64);
      const bytes = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
      const blob = new Blob([bytes], { type: 'application/vnd.frek.culture+zip' });
      const url = URL.createObjectURL(blob);
      setDownloadUrl(url);
      setResult(data.info);
      setPhase('done');
    } catch (e) {
      setError(e.message || 'Erreur.');
      setPhase('error');
    }
  };

  const reset = () => {
    if (downloadUrl) URL.revokeObjectURL(downloadUrl);
    setForm({ title: '', object_type: 'song', primary_creator_name: '', description: '', keep: false });
    setFiles([]);
    setResult(null);
    setDownloadUrl(null);
    setError('');
    setPhase('idle');
  };

  if (phase === 'done' && result) {
    return (
      <motion.div
        key="done"
        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        className="bg-white/70 backdrop-blur-xl border border-white/50 rounded-3xl p-8 shadow-xl"
        data-testid="fk-create-done"
      >
        <div className="text-center mb-6">
          <div className="text-6xl mb-3">✓</div>
          <h2 className="text-2xl font-black text-slate-900 tracking-tight">Objet culturel vérifiable.</h2>
          <p className="text-sm text-slate-600 mt-2 max-w-md mx-auto" data-testid="fk-result-tagline">
            Un objet FK — pas une archive technique. Il transporte son identité, son histoire et sa preuve à travers le temps.
          </p>
          <p className="text-xs text-slate-400 font-mono mt-3" data-testid="fk-result-id">{result.frek_id}</p>
        </div>
        <dl className="space-y-3 text-sm">
          <MetaRow label="Titre" value={result.title} />
          <MetaRow label="Type" value={result.object_type} />
          <MetaRow label="Créateur" value={result.creator} />
          <MetaRow label="Médias" value={String(result.media_count)} />
          <MetaRow label="Taille" value={`${(result.size_bytes / 1024).toFixed(1)} Ko`} />
          {result.block_hash && (
            <MetaRow label="Block FREK-Chain" mono value={result.block_hash} />
          )}
          <MetaRow label="Empreinte racine" mono value={result.root_hash} />
        </dl>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <a
            href={downloadUrl}
            download={`${result.title.replace(/\s+/g, '_').slice(0, 40) || 'creation'}.fk.zip`}
            className="px-6 py-3 bg-slate-900 text-white rounded-full font-semibold shadow-lg hover:bg-slate-700 transition-colors"
            data-testid="fk-export-btn"
          >
            Télécharger (.fk.zip)
          </a>
          <Link
            to={`/fk/view/${result.frek_id}`}
            className="px-6 py-3 bg-blue-50 border border-blue-200 text-blue-900 rounded-full font-semibold hover:bg-blue-100 transition-colors"
            data-testid="fk-open-viewer"
          >
            Ouvrir dans le lecteur
          </Link>
          <button
            onClick={reset}
            className="px-6 py-3 bg-white/70 border border-slate-300 text-slate-900 rounded-full font-semibold hover:bg-white transition-colors"
            data-testid="fk-create-another"
          >
            Créer un autre
          </button>
        </div>
        <p className="text-xs text-slate-500 mt-6 text-center">
          Ce fichier <code className="font-mono">.fk</code> est signé cryptographiquement. Il peut être vérifié hors ligne, sans FREKCORE, à vie.
        </p>
      </motion.div>
    );
  }

  return (
    <motion.div
      key="create"
      initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
      className="bg-white/70 backdrop-blur-xl border border-white/50 rounded-3xl p-8 shadow-xl space-y-5"
      data-testid="fk-create-form"
    >
      <Field label="Titre de l'œuvre / de l'événement *">
        <input
          type="text" value={form.title}
          onChange={(e) => setForm({ ...form, title: e.target.value })}
          maxLength={200}
          className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          placeholder="Ex : Concert Bataclan — 12 mars 2026"
          data-testid="fk-input-title"
        />
      </Field>

      <div className="grid md:grid-cols-2 gap-4">
        <Field label="Type d'objet">
          <select
            value={form.object_type}
            onChange={(e) => setForm({ ...form, object_type: e.target.value })}
            className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 bg-white"
            data-testid="fk-input-object-type"
          >
            {OBJECT_TYPES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </Field>
        <Field label="Créateur principal *">
          <input
            type="text" value={form.primary_creator_name}
            onChange={(e) => setForm({ ...form, primary_creator_name: e.target.value })}
            maxLength={120}
            className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            placeholder="Nom ou institution"
            data-testid="fk-input-creator"
          />
        </Field>
      </div>

      <Field label="Description (optionnel)">
        <textarea
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
          rows={2} maxLength={600}
          className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          placeholder="Contexte, intention, note..."
          data-testid="fk-input-description"
        />
      </Field>

      <Field label="Médias (audio, image, vidéo, PDF...)">
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="w-full py-4 border-2 border-dashed border-slate-300 rounded-xl text-slate-600 hover:border-blue-400 hover:text-blue-600 transition-colors text-sm"
          data-testid="fk-add-files"
        >
          + Ajouter un ou plusieurs fichiers
        </button>
        <input
          ref={fileInputRef} type="file" multiple className="hidden"
          onChange={onFiles}
          data-testid="fk-files-input"
        />
        {files.length > 0 && (
          <div className="mt-3 space-y-2" data-testid="fk-files-list">
            {files.map((f, i) => (
              <div key={i} className="flex items-center justify-between bg-blue-50/70 border border-blue-100 rounded-lg px-3 py-2 text-sm">
                <span className="truncate text-slate-800">{f.name}</span>
                <div className="flex items-center gap-3 shrink-0">
                  <span className="text-xs text-slate-500">{(f.size / 1024).toFixed(1)} Ko</span>
                  <button onClick={() => removeFile(i)} className="text-slate-400 hover:text-red-600 text-lg leading-none" aria-label="Retirer">×</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Field>

      <label className="flex items-center gap-2 text-sm text-slate-700 cursor-pointer" data-testid="fk-keep-toggle">
        <input
          type="checkbox" checked={form.keep}
          onChange={(e) => setForm({ ...form, keep: e.target.checked })}
          className="w-4 h-4 accent-blue-600"
        />
        <span>Conserver une copie chiffrée côté FREKCORE (permet le re-téléchargement).</span>
      </label>

      {error && (
        <p className="text-red-600 text-sm" data-testid="fk-error">{error}</p>
      )}

      <div className="flex justify-center pt-2">
        <motion.button
          whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
          onClick={submit}
          disabled={phase === 'creating'}
          className="px-8 py-4 bg-slate-900 text-white rounded-full font-semibold shadow-lg hover:bg-slate-700 disabled:opacity-60 transition-colors"
          data-testid="fk-create-btn"
        >
          {phase === 'creating' ? 'Création en cours…' : 'Créer l\'objet culturel FK'}
        </motion.button>
      </div>
    </motion.div>
  );
}

function Field({ label, children }) {
  return (
    <div>
      <label className="block text-xs uppercase tracking-[0.2em] text-slate-500 mb-2">{label}</label>
      {children}
    </div>
  );
}

function MetaRow({ label, value, mono }) {
  return (
    <div className="flex flex-col">
      <span className="text-[10px] uppercase tracking-[0.2em] text-slate-400">{label}</span>
      <span className={`text-slate-900 ${mono ? 'font-mono text-xs break-all' : ''}`}>{value || '—'}</span>
    </div>
  );
}

// ---------------- VERIFY ----------------

function VerifyFK() {
  const [file, setFile] = useState(null);
  const [phase, setPhase] = useState('idle'); // idle | verifying | done | error
  const [report, setReport] = useState(null);
  const [error, setError] = useState('');
  const inputRef = useRef(null);

  const onFile = (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    setReport(null);
    setError('');
    setPhase('idle');
  };

  const verify = async () => {
    if (!file) return;
    setPhase('verifying');
    setError('');
    try {
      const fd = new FormData();
      fd.append('file', file);
      const res = await fetch(`${API}/api/v1/fk/verify`, { method: 'POST', body: fd });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setReport(await res.json());
      setPhase('done');
    } catch (e) {
      setError(e.message || 'Erreur de vérification');
      setPhase('error');
    }
  };

  return (
    <motion.div
      key="verify"
      initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
      className="bg-white/70 backdrop-blur-xl border border-white/50 rounded-3xl p-8 shadow-xl"
      data-testid="fk-verify-panel"
    >
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        className="w-full py-8 border-2 border-dashed border-slate-300 rounded-xl text-slate-600 hover:border-blue-400 hover:text-blue-600 transition-colors text-sm"
        data-testid="fk-verify-drop"
      >
        {file ? file.name : 'Sélectionne un fichier .fk à vérifier'}
      </button>
      <input
        ref={inputRef} type="file" accept=".fk,application/vnd.frek.culture+zip,application/zip"
        className="hidden" onChange={onFile}
        data-testid="fk-verify-input"
      />

      {file && phase !== 'done' && (
        <div className="mt-5 flex justify-center">
          <button
            onClick={verify} disabled={phase === 'verifying'}
            className="px-6 py-3 bg-slate-900 text-white rounded-full font-semibold shadow-lg hover:bg-slate-700 disabled:opacity-60 transition-colors"
            data-testid="fk-verify-btn"
          >
            {phase === 'verifying' ? 'Vérification…' : 'Vérifier l\'authenticité'}
          </button>
        </div>
      )}

      {error && <p className="text-red-600 text-sm mt-4" data-testid="fk-verify-error">{error}</p>}

      {report && (
        <motion.div
          initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
          className="mt-6 space-y-4"
          data-testid="fk-verify-report"
        >
          <div className={`text-center py-4 rounded-2xl border ${
            report.valid
              ? 'bg-blue-50 border-blue-200 text-blue-900'
              : 'bg-red-50 border-red-200 text-red-900'
          }`}>
            <div className="text-3xl mb-1">{report.valid ? '✓' : '⚠'}</div>
            <p className="font-semibold" data-testid="fk-verify-verdict">
              {report.valid ? 'Objet FK authentique' : 'Objet FK non valide'}
            </p>
            <p className="text-xs mt-1 opacity-70">{report.summary}</p>
          </div>

          {report.valid && (
            <dl className="space-y-3 text-sm border-t pt-4">
              <MetaRow label="FREK-ID" value={report.frek_id} mono />
              <MetaRow label="Titre" value={report.title} />
              <MetaRow label="Type" value={report.object_type} />
              <MetaRow label="Créateur" value={report.creator} />
              <MetaRow label="Médias" value={String(report.media_count)} />
              {report.block_hash && <MetaRow label="Block FREK-Chain" value={report.block_hash} mono />}
              <MetaRow label="Signature" value={report.signature_algo || '—'} />
            </dl>
          )}

          <details className="text-xs text-slate-600">
            <summary className="cursor-pointer hover:text-slate-900" data-testid="fk-verify-details-toggle">
              Voir le détail des contrôles ({report.checks?.length || 0})
            </summary>
            <ul className="mt-2 space-y-1 font-mono text-[11px]">
              {report.checks?.map((c) => (
                <li key={c.check} className={c.ok ? 'text-green-700' : 'text-red-700'}>
                  {c.ok ? '✓' : '✗'} {c.check}{c.detail ? ` — ${c.detail.slice(0, 90)}` : ''}
                </li>
              ))}
            </ul>
          </details>
        </motion.div>
      )}
    </motion.div>
  );
}
