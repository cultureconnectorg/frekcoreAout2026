import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import JSZip from 'jszip';
import BrandLogo from '../components/BrandLogo';

/**
 * FREKCORE — Lecteur FK en navigateur.
 *
 * Le format .fk est un ZIP a extension inconnue. iOS Safari ne sait pas
 * l'ouvrir : ce lecteur charge le fichier cote client via JSZip et affiche
 * son contenu de facon lisible (manifest, medias, signature).
 *
 * Deux usages :
 *   /fk/view/:frek_id   — charge depuis le serveur (si keep=true)
 *   /fk/view (sans id)  — upload local
 */

const API = import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;

async function readFK(bytes) {
  const zip = await JSZip.loadAsync(bytes);
  const files = [];
  let manifest = null;
  let signature = null;
  let root = null;
  let identity = null;
  let creators = null;
  let timeline = null;
  for (const name of Object.keys(zip.files)) {
    const entry = zip.files[name];
    if (entry.dir) continue;
    const lower = name.toLowerCase();
    // Manifest racine (FREKCORE FK v0.1 : manifest.fk.json)
    if (lower === 'manifest.fk.json' || lower === 'manifest.json') {
      manifest = JSON.parse(await entry.async('string'));
    } else if (lower === 'metadata/identity.json') {
      identity = JSON.parse(await entry.async('string'));
    } else if (lower === 'metadata/creators.json') {
      creators = JSON.parse(await entry.async('string'));
    } else if (lower === 'metadata/timeline.json') {
      timeline = JSON.parse(await entry.async('string'));
    } else if (lower === 'proof/frekcore-attestation.json' || lower.endsWith('/signature.json')) {
      signature = JSON.parse(await entry.async('string'));
      // Normalisation : le fichier proof FREKCORE est un JSON plat qui contient
      // root_hash + public_key_* directement. On dérive root et alias pubkey pour
      // rester compatible avec les FK d'autres implémentations.
      if (signature && signature.root_hash && !root) {
        root = { root_hash: signature.root_hash };
      }
      if (signature && !signature.pubkey) {
        signature.pubkey = signature.public_key_raw_b64 || signature.public_key_pem;
      }
    } else if (lower.endsWith('root.json') || lower.endsWith('proof.json')) {
      root = JSON.parse(await entry.async('string'));
    } else if (lower === 'media/media.json' || lower.endsWith('/media.json')) {
      // Media manifest ignored — vrais medias listés via files[]
    } else if (lower === 'readme.txt' || lower === 'intelligence/intelligence.json' || lower === 'rights/ownership.json') {
      // Skip meta layers, non pertinents pour affichage
    } else if (lower.startsWith('media/')) {
      const blob = await entry.async('blob');
      files.push({ name, size: blob.size, type: blob.type || guessType(name), blob });
    } else {
      const blob = await entry.async('blob');
      files.push({ name, size: blob.size, type: blob.type || guessType(name), blob });
    }
  }
  // Compose une vue enrichie du manifest avec les layers metadata
  const merged = manifest ? {
    ...manifest,
    title: identity?.title || manifest.title,
    description: identity?.description || manifest.description,
    creator: creators?.primary_creator?.name || creators?.primary_creator_name || creators?.primary_creator || manifest.creator,
    creators_list: creators?.contributors || creators?.list || [],
    created_at: manifest.created_at || timeline?.created_at,
    timeline,
  } : null;
  return { manifest: merged, signature, root, files, identity, creators };
}

function guessType(name) {
  const ext = name.split('.').pop().toLowerCase();
  return {
    jpg: 'image/jpeg', jpeg: 'image/jpeg', png: 'image/png', gif: 'image/gif',
    webp: 'image/webp', mp3: 'audio/mpeg', m4a: 'audio/mp4', wav: 'audio/wav',
    mp4: 'video/mp4', mov: 'video/quicktime', pdf: 'application/pdf',
    txt: 'text/plain', json: 'application/json',
  }[ext] || 'application/octet-stream';
}

export default function FKView() {
  const { id } = useParams();
  const [state, setState] = useState({ phase: 'loading', report: null, error: '' });
  const [previews, setPreviews] = useState({});
  const [reportServer, setReportServer] = useState(null);

  useEffect(() => {
    if (!id) { setState({ phase: 'idle', report: null, error: '' }); return; }
    let cancel = false;
    (async () => {
      try {
        // ?compat=zip evite les blocages iOS sur l'extension .fk
        const dlUrl = `${API}/api/v1/fk/${id}/download?compat=zip`;
        const res = await fetch(dlUrl);
        if (!res.ok) {
          if (res.status === 404) throw new Error('Objet FK introuvable ou non conservé côté serveur.');
          throw new Error(`Erreur ${res.status}`);
        }
        const bytes = await res.arrayBuffer();
        const parsed = await readFK(bytes);
        if (cancel) return;
        setState({ phase: 'ready', report: { ...parsed, size: bytes.byteLength, source: 'server', downloadUrl: dlUrl }, error: '' });
        // Verif backend en parallele
        try {
          const fd = new FormData();
          fd.append('file', new Blob([bytes], { type: 'application/zip' }), `${id}.fk`);
          const vr = await fetch(`${API}/api/v1/fk/verify`, { method: 'POST', body: fd });
          if (vr.ok) {
            const rep = await vr.json();
            if (!cancel) setReportServer(rep);
          }
        } catch { /* silent */ }
      } catch (e) {
        if (!cancel) setState({ phase: 'error', report: null, error: e.message || 'Erreur' });
      }
    })();
    return () => { cancel = true; };
  }, [id]);

  const loadLocal = async (file) => {
    setState({ phase: 'loading', report: null, error: '' });
    try {
      const bytes = await file.arrayBuffer();
      const parsed = await readFK(bytes);
      setState({ phase: 'ready', report: { ...parsed, size: bytes.byteLength, source: 'local', filename: file.name }, error: '' });
    } catch (e) {
      setState({ phase: 'error', report: null, error: `Impossible de lire ce fichier : ${e.message}` });
    }
  };

  useEffect(() => {
    // Genere previews pour images/audio
    if (state.phase !== 'ready') return;
    const urls = {};
    state.report.files.forEach((f) => {
      if (f.type.startsWith('image/') || f.type.startsWith('audio/') || f.type.startsWith('video/')) {
        urls[f.name] = URL.createObjectURL(f.blob);
      }
    });
    setPreviews(urls);
    return () => { Object.values(urls).forEach((u) => URL.revokeObjectURL(u)); };
  }, [state]);

  return (
    <div className="relative min-h-screen bg-gradient-to-br from-white via-blue-50 to-blue-100 flex flex-col overflow-hidden">
      <motion.header
        initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
        className="relative z-10 p-6 flex justify-between items-center max-w-5xl mx-auto w-full"
      >
        <BrandLogo to="/universe" testId="fkview-brand" />
        <nav className="flex gap-6 text-sm text-slate-600">
          <Link to="/universe" className="hover:text-blue-600 transition-colors" data-testid="fkview-link-universe">Univers</Link>
          <Link to="/fk" className="hover:text-blue-600 transition-colors" data-testid="fkview-link-fk">Créer un FK</Link>
          <Link to="/spec" className="hover:text-blue-600 transition-colors" data-testid="fkview-link-spec">Charte</Link>
        </nav>
      </motion.header>

      <main className="relative z-10 flex-1 max-w-3xl mx-auto w-full px-6 py-10">
        <p className="text-xs text-slate-500 uppercase tracking-[0.3em] mb-3">Lecteur d&apos;objet culturel FK</p>
        <h1 className="text-4xl md:text-5xl font-black tracking-tighter text-slate-900 mb-4" data-testid="fkview-headline">
          Ouvrir un objet FK.
        </h1>
        <p className="text-slate-600 max-w-xl mb-8 leading-relaxed">
          Lit un objet culturel <b>directement dans votre navigateur</b> — utile sur iPhone, iPad ou tout appareil qui ne reconnaît pas l&apos;extension <code className="font-mono">.fk</code>.
        </p>

        {state.phase === 'loading' && (
          <div className="flex items-center justify-center py-16" data-testid="fkview-loading">
            <div className="w-10 h-10 border-2 border-slate-200 border-t-blue-600 rounded-full animate-spin" />
          </div>
        )}

        {state.phase === 'error' && (
          <div className="bg-red-50 border border-red-200 rounded-2xl p-6 text-center" data-testid="fkview-error">
            <p className="text-red-800 font-semibold mb-2">Erreur de lecture</p>
            <p className="text-sm text-red-700">{state.error}</p>
          </div>
        )}

        {(state.phase === 'idle' || (state.phase === 'error' && !id)) && (
          <div className="bg-white/70 backdrop-blur border border-blue-200 rounded-2xl p-6" data-testid="fkview-uploader">
            <label className="block text-sm text-slate-700 mb-3 cursor-pointer">
              <span className="block mb-3">Sélectionnez un fichier <code className="font-mono">.fk</code> ou <code className="font-mono">.fk.zip</code> pour l&apos;ouvrir localement.</span>
              <input
                type="file" accept=".fk,.zip,.fkzip"
                onChange={(e) => e.target.files?.[0] && loadLocal(e.target.files[0])}
                className="text-sm text-slate-700"
                data-testid="fkview-upload-input"
              />
            </label>
          </div>
        )}

        {state.phase === 'ready' && state.report && (
          <div className="space-y-6" data-testid="fkview-report">
            {/* Manifest / identity */}
            <div className="bg-white/80 backdrop-blur-xl border border-white/60 rounded-2xl p-6 shadow-lg" data-testid="fkview-manifest">
              <div className="text-[10px] uppercase tracking-[0.25em] text-blue-600 mb-2">Objet culturel</div>
              <h2 className="text-2xl font-black text-slate-900 tracking-tight mb-4" data-testid="fkview-title">
                {state.report.manifest?.title || state.report.manifest?.metadata?.title || 'Objet FK sans titre'}
              </h2>
              <dl className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
                <Meta label="Type" value={state.report.manifest?.object_type} />
                <Meta label="Créateur déclaré" value={state.report.manifest?.creator || state.report.manifest?.primary_creator_name} />
                <Meta label="FREK-ID" mono value={state.report.manifest?.frek_id} />
                <Meta label="Créé le" value={fmtDate(state.report.manifest?.created_at)} />
                <Meta label="Médias" value={String(state.report.files.length)} />
                <Meta label="Taille" value={`${(state.report.size / 1024).toFixed(1)} Ko`} />
              </dl>
              {state.report.manifest?.description && (
                <p className="mt-4 pt-4 border-t border-slate-100 text-sm text-slate-700 leading-relaxed" data-testid="fkview-description">
                  {state.report.manifest.description}
                </p>
              )}
            </div>

            {/* Signature + verify */}
            <div className="bg-white/80 backdrop-blur-xl border border-white/60 rounded-2xl p-6 shadow-lg" data-testid="fkview-signature">
              <div className="text-[10px] uppercase tracking-[0.25em] text-blue-600 mb-2">Signature & preuve</div>
              {reportServer ? (
                <div className={`text-sm font-semibold mb-3 ${reportServer.valid ? 'text-blue-700' : 'text-red-700'}`} data-testid="fkview-verify-status">
                  {reportServer.valid ? '✓ Signature vérifiée par le nœud FREKCORE' : '⚠ Signature invalide ou altérée'}
                </div>
              ) : (
                <div className="text-xs text-slate-500 mb-3" data-testid="fkview-verify-pending">
                  Vérification côté serveur en cours ou indisponible. La signature ci-dessous peut aussi être vérifiée hors-ligne via <Link to="/verifier" className="text-blue-600 hover:underline">le vérificateur Python/JS</Link>.
                </div>
              )}
              <dl className="grid grid-cols-1 gap-2 text-xs">
                {state.report.root?.root_hash && <Meta label="Empreinte racine" mono value={state.report.root.root_hash} />}
                {state.report.signature?.signature && <Meta label="Signature Ed25519" mono value={state.report.signature.signature.slice(0, 32) + '…'} />}
                {state.report.signature?.pubkey && <Meta label="Clé publique" mono value={state.report.signature.pubkey.slice(0, 32) + '…'} />}
                {state.report.manifest?.block_hash && <Meta label="Bloc FREK-Chain" mono value={state.report.manifest.block_hash} />}
              </dl>
            </div>

            {/* Fichiers */}
            <div className="bg-white/80 backdrop-blur-xl border border-white/60 rounded-2xl p-6 shadow-lg" data-testid="fkview-files">
              <div className="text-[10px] uppercase tracking-[0.25em] text-blue-600 mb-4">Contenu</div>
              {state.report.files.length === 0 ? (
                <p className="text-sm text-slate-500 italic">Aucun média joint.</p>
              ) : (
                <ul className="space-y-4">
                  {state.report.files.map((f) => (
                    <li key={f.name} className="border-t border-slate-100 pt-4 first:border-t-0 first:pt-0" data-testid={`fkview-file-${f.name}`}>
                      <div className="flex items-baseline justify-between gap-3 mb-2">
                        <span className="font-mono text-xs text-slate-700 truncate">{f.name}</span>
                        <span className="text-[10px] text-slate-400 shrink-0">{(f.size / 1024).toFixed(1)} Ko · {f.type}</span>
                      </div>
                      {previews[f.name] && f.type.startsWith('image/') && (
                        <img src={previews[f.name]} alt={f.name} className="max-w-full rounded-lg border border-slate-200" loading="lazy" />
                      )}
                      {previews[f.name] && f.type.startsWith('audio/') && (
                        <audio controls src={previews[f.name]} className="w-full" />
                      )}
                      {previews[f.name] && f.type.startsWith('video/') && (
                        <video controls src={previews[f.name]} className="max-w-full rounded-lg" />
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* Download link (avec .fk.zip pour iOS) */}
            {state.report.source === 'server' && state.report.downloadUrl && (
              <div className="text-center">
                <a
                  href={state.report.downloadUrl}
                  download
                  className="inline-block px-6 py-3 bg-slate-900 text-white rounded-full font-semibold shadow hover:bg-slate-700 transition-colors"
                  data-testid="fkview-download-zip"
                >
                  Télécharger le fichier (.fk.zip)
                </a>
                <p className="text-[10px] text-slate-500 mt-2">
                  L&apos;extension .zip est reconnue par iOS et Android — l&apos;objet reste identique.
                </p>
              </div>
            )}
          </div>
        )}
      </main>

      <footer className="relative z-10 p-6 text-center text-xs text-slate-400" data-testid="fkview-legal-notice">
        FREKCORE atteste l&apos;existence, l&apos;intégrité et l&apos;origine déclarée d&apos;un objet numérique.
      </footer>
    </div>
  );
}

function Meta({ label, value, mono }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-[0.2em] text-slate-400 mb-0.5">{label}</div>
      <div className={`text-slate-900 ${mono ? 'font-mono text-[11px] break-all' : ''}`}>{value || '—'}</div>
    </div>
  );
}

function fmtDate(iso) {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleString('fr-FR', { dateStyle: 'medium', timeStyle: 'short' });
  } catch { return iso; }
}
