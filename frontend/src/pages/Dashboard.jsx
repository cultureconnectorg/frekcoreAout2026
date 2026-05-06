/**
 * CC2026 Monitor Operationnel — Dashboard Luciole
 * Theme: meme couleurs que le site FREK (white/glassmorphism/blue #2cc4f5)
 */
import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { motion, useMotionValue, useTransform, useSpring } from 'framer-motion';

const API_URL = import.meta.env.VITE_BACKEND_URL || '';

const STAGES = ['GENESIS', 'WORKSHOP', 'METAMORPHOSE', 'EMISSION', 'LEGACY'];
const STAGE_COLORS = {
  GENESIS: '#2cc4f5',
  WORKSHOP: '#06b6d4',
  METAMORPHOSE: '#8B5CF6',
  EMISSION: '#F59E0B',
  LEGACY: '#10B981',
};
const STAGE_ICONS = {
  GENESIS: 'fa-seedling',
  WORKSHOP: 'fa-hammer',
  METAMORPHOSE: 'fa-exchange-alt',
  EMISSION: 'fa-broadcast-tower',
  LEGACY: 'fa-archive',
};

function PulseIndicator({ active }) {
  return (
    <span className="relative flex h-2 w-2">
      {active && (
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
      )}
      <span className={`relative inline-flex rounded-full h-2 w-2 ${active ? 'bg-emerald-400' : 'bg-red-400'}`} />
    </span>
  );
}

function ProgressRing({ percentage, size = 130, strokeWidth = 8 }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percentage / 100) * circumference;

  return (
    <svg width={size} height={size} className="transform -rotate-90">
      <circle cx={size/2} cy={size/2} r={radius} fill="none" stroke="#e2e8f0" strokeWidth={strokeWidth} />
      <motion.circle
        cx={size/2} cy={size/2} r={radius} fill="none"
        stroke="url(#blueGrad)" strokeWidth={strokeWidth} strokeLinecap="round"
        initial={{ strokeDashoffset: circumference }}
        animate={{ strokeDashoffset: offset }}
        transition={{ duration: 1.5, ease: 'easeOut' }}
        strokeDasharray={circumference}
      />
      <defs>
        <linearGradient id="blueGrad" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#2cc4f5" />
          <stop offset="100%" stopColor="#06b6d4" />
        </linearGradient>
      </defs>
    </svg>
  );
}

function GlassCard({ children, className = '', delay = 0, ...props }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      className={`bg-white/70 backdrop-blur-2xl rounded-2xl border border-white/50 shadow-lg shadow-slate-200/50 ${className}`}
      {...props}
    >
      {children}
    </motion.div>
  );
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [live, setLive] = useState(null);
  const [notary, setNotary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  // Parallax
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  const smoothX = useSpring(mouseX, { stiffness: 50, damping: 20 });
  const smoothY = useSpring(mouseY, { stiffness: 50, damping: 20 });
  const bgX = useTransform(smoothX, [0, typeof window !== 'undefined' ? window.innerWidth : 1920], [-15, 15]);
  const bgY = useTransform(smoothY, [0, typeof window !== 'undefined' ? window.innerHeight : 800], [-15, 15]);

  useEffect(() => {
    const h = (e) => { mouseX.set(e.clientX); mouseY.set(e.clientY); };
    window.addEventListener('mousemove', h);
    return () => window.removeEventListener('mousemove', h);
  }, [mouseX, mouseY]);

  const fetchDashboard = useCallback(async () => {
    try {
      const resp = await fetch(`${API_URL}/api/v1/dashboard/cc2026`);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      setData(await resp.json());
      setError(null);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }, []);

  const fetchLive = useCallback(async () => {
    try {
      const resp = await fetch(`${API_URL}/api/v1/dashboard/cc2026/live`);
      if (!resp.ok) return;
      setLive(await resp.json());
      setLastUpdate(new Date());
    } catch {}
  }, []);

  const fetchNotary = useCallback(async () => {
    try {
      const resp = await fetch(`${API_URL}/api/v1/notary/chain/status`);
      if (!resp.ok) return;
      setNotary(await resp.json());
    } catch {}
  }, []);

  useEffect(() => {
    fetchDashboard();
    fetchLive();
    fetchNotary();
    const i = setInterval(() => { fetchLive(); fetchNotary(); }, 5000);
    return () => clearInterval(i);
  }, [fetchDashboard, fetchLive, fetchNotary]);

  const metrics = data?.metrics || {};
  const total = live?.total ?? metrics.total_identities ?? 0;
  const active = live?.active ?? metrics.active_identities ?? 0;
  const pct = live?.percentage ?? metrics.progression_percent ?? 0;
  const funnel = data?.luciole_funnel || [];
  const timeline = data?.timeline_30d || [];
  const clientsActivity = data?.clients_activity || {};

  if (loading) {
    return (
      <div className="min-h-screen bg-[#f8fafc] flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          className="w-10 h-10 border-2 border-[#2cc4f5] border-t-transparent rounded-full"
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-800 relative overflow-hidden" data-testid="dashboard-cc2026">
      {/* Animated Background */}
      <motion.div className="absolute inset-0 overflow-hidden pointer-events-none" style={{ x: bgX, y: bgY }}>
        <motion.div
          animate={{ scale: [1, 1.2, 1], opacity: [0.12, 0.22, 0.12] }}
          transition={{ repeat: Infinity, duration: 8, ease: 'easeInOut' }}
          className="absolute -top-32 -right-32 w-[500px] h-[500px] bg-gradient-to-br from-[#2cc4f5] to-[#06b6d4] rounded-full blur-3xl"
        />
        <motion.div
          animate={{ scale: [1, 1.15, 1], opacity: [0.08, 0.18, 0.08] }}
          transition={{ repeat: Infinity, duration: 10, ease: 'easeInOut', delay: 2 }}
          className="absolute -bottom-40 -left-40 w-[600px] h-[600px] bg-gradient-to-tr from-[#0ea5e9] to-[#2cc4f5] rounded-full blur-3xl"
        />
        <div
          className="absolute inset-0 opacity-[0.02]"
          style={{
            backgroundImage: 'linear-gradient(to right, #2cc4f5 1px, transparent 1px), linear-gradient(to bottom, #2cc4f5 1px, transparent 1px)',
            backgroundSize: '80px 80px'
          }}
        />
      </motion.div>

      {/* Header — meme style que Certify */}
      <header className="fixed top-0 left-0 right-0 z-50" data-testid="dashboard-header">
        <motion.div
          initial={{ y: -20, opacity: 0 }} animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
          className="mx-4 sm:mx-6 mt-4"
        >
          <div className="max-w-6xl mx-auto bg-white/70 backdrop-blur-2xl rounded-2xl border border-white/50 shadow-lg shadow-slate-200/50 px-4 sm:px-6 h-14 sm:h-16 flex items-center justify-between">
            <Link to="/" className="flex items-center gap-2 group">
              <img src="/frek-logo.png" alt="FREK" className="h-7 sm:h-8 w-auto" />
              <span className="font-display text-xl tracking-wider bg-gradient-to-r from-[#2cc4f5] to-[#0ea5e9] bg-clip-text text-transparent font-semibold">
                FREK
              </span>
            </Link>
            <div className="flex items-center gap-3 sm:gap-5">
              <h1 className="font-mono text-[10px] sm:text-xs uppercase tracking-widest text-slate-400">
                CC2026 Monitor
              </h1>
              <div className="flex items-center gap-2 px-3 py-1 bg-[#2cc4f5]/5 rounded-xl border border-[#2cc4f5]/15 text-[10px] sm:text-xs" data-testid="system-status">
                <PulseIndicator active={!error} />
                <span className="text-[#2cc4f5] font-mono">v2.0</span>
              </div>
              {lastUpdate && (
                <span className="text-[10px] text-slate-300 font-mono hidden sm:block">
                  {lastUpdate.toLocaleTimeString('fr-FR')}
                </span>
              )}
            </div>
          </div>
        </motion.div>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 pt-28 pb-12 relative z-10 space-y-6">
        {error && (
          <div className="bg-red-50/80 backdrop-blur-sm border border-red-200 rounded-xl px-4 py-3 text-red-600 text-sm" data-testid="error-banner">
            <i className="fas fa-exclamation-triangle mr-2" />{error}
          </div>
        )}

        {/* ROW 1 — Metriques principales */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
          {/* Progression ring */}
          <GlassCard className="md:col-span-2 p-6 sm:p-8 flex items-center gap-6 sm:gap-8" delay={0} data-testid="widget-progression">
            <div className="relative flex-shrink-0">
              <ProgressRing percentage={pct} size={120} strokeWidth={8} />
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-2xl sm:text-3xl font-display bg-gradient-to-r from-[#2cc4f5] to-[#06b6d4] bg-clip-text text-transparent">{pct}%</span>
                <span className="text-[9px] text-slate-400 uppercase tracking-wider font-mono">objectif</span>
              </div>
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-mono text-[10px] sm:text-xs text-slate-400 uppercase tracking-widest mb-1">Identites CC2026</p>
              <div className="text-4xl sm:text-5xl font-display tracking-wide text-slate-800" data-testid="total-identities">
                {total.toLocaleString('fr-FR')}
              </div>
              <div className="mt-3 w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                <motion.div
                  className="h-full rounded-full bg-gradient-to-r from-[#2cc4f5] to-[#06b6d4]"
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(pct, 100)}%` }}
                  transition={{ duration: 1.2, ease: 'easeOut' }}
                />
              </div>
              <p className="text-[10px] sm:text-xs mt-2 text-slate-400 font-mono">
                {(40000 - total).toLocaleString('fr-FR')} restants sur 40 000
              </p>
            </div>
          </GlassCard>

          {/* Actifs */}
          <GlassCard className="p-6" delay={0.08} data-testid="widget-active">
            <p className="font-mono text-[10px] text-slate-400 uppercase tracking-widest mb-3">Actives</p>
            <div className="text-4xl font-display bg-gradient-to-r from-emerald-400 to-emerald-500 bg-clip-text text-transparent">
              {active.toLocaleString('fr-FR')}
            </div>
            <div className="mt-3 flex items-center gap-2 text-[10px] text-emerald-500/70 font-mono">
              <PulseIndicator active />
              <span>Scan physique</span>
            </div>
          </GlassCard>

          {/* Clients */}
          <GlassCard className="p-6" delay={0.12} data-testid="widget-clients">
            <p className="font-mono text-[10px] text-slate-400 uppercase tracking-widest mb-3">Clients API</p>
            <div className="text-4xl font-display text-[#2cc4f5]">
              {Object.keys(clientsActivity).length}
            </div>
            <div className="mt-3 space-y-1">
              {Object.entries(clientsActivity).slice(0, 3).map(([id, count]) => (
                <div key={id} className="flex justify-between text-[10px] font-mono">
                  <span className="text-slate-400 truncate mr-2">{id}</span>
                  <span className="text-slate-600">{count}</span>
                </div>
              ))}
            </div>
          </GlassCard>
        </div>

        {/* ROW 2 — Funnel Luciole */}
        <GlassCard className="p-6 sm:p-8" delay={0.16} data-testid="widget-funnel">
          <p className="font-mono text-[10px] text-slate-400 uppercase tracking-widest mb-6">
            Funnel Luciole — 5 Stages
          </p>
          <div className="grid grid-cols-5 gap-3 sm:gap-5">
            {STAGES.map((stage, i) => {
              const count = funnel.find(f => f.stage === stage)?.count || 0;
              const maxCount = Math.max(...funnel.map(f => f.count), 1);
              const pctBar = (count / maxCount) * 100;

              return (
                <motion.div
                  key={stage}
                  initial={{ opacity: 0, y: 24 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.25 + i * 0.06 }}
                  className="text-center"
                >
                  <div className="h-28 flex flex-col justify-end mb-2">
                    <motion.div
                      className="rounded-xl mx-auto w-full max-w-[50px] overflow-hidden"
                      style={{ backgroundColor: STAGE_COLORS[stage] + '15' }}
                      initial={{ height: 0 }}
                      animate={{ height: `${Math.max(pctBar, 10)}%` }}
                      transition={{ duration: 0.8, delay: 0.35 + i * 0.08 }}
                    >
                      <div
                        className="w-full h-full rounded-xl"
                        style={{ backgroundColor: STAGE_COLORS[stage], opacity: 0.7 }}
                      />
                    </motion.div>
                  </div>
                  <div className="text-xl sm:text-2xl font-display" style={{ color: STAGE_COLORS[stage] }}>
                    {count}
                  </div>
                  <div className="text-[8px] sm:text-[9px] text-slate-400 uppercase tracking-wider mt-0.5 font-mono flex items-center justify-center gap-1">
                    <i className={`fas ${STAGE_ICONS[stage]}`} style={{ color: STAGE_COLORS[stage], fontSize: '7px' }} />
                    <span className="hidden sm:inline">{stage}</span>
                    <span className="sm:hidden">{stage.slice(0,3)}</span>
                  </div>
                </motion.div>
              );
            })}
          </div>
          {/* Flow indicator */}
          <div className="mt-5 flex items-center justify-center gap-1.5">
            {STAGES.map((stage, i) => (
              <div key={stage} className="flex items-center gap-1">
                {i > 0 && <i className="fas fa-chevron-right text-[7px] text-slate-300 mx-0.5" />}
                <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: STAGE_COLORS[stage] }} />
              </div>
            ))}
          </div>
        </GlassCard>

        {/* ROW 3 — Timeline + Live */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <GlassCard className="p-6" delay={0.2} data-testid="widget-timeline">
            <p className="font-mono text-[10px] text-slate-400 uppercase tracking-widest mb-4">
              Activite 30 jours
            </p>
            {timeline.length > 0 ? (
              <div className="flex items-end gap-[2px] h-20">
                {timeline.map((d, i) => {
                  const maxVal = Math.max(...timeline.map(t => t.stages_recorded), 1);
                  const h = (d.stages_recorded / maxVal) * 100;
                  return (
                    <motion.div
                      key={d.date}
                      initial={{ height: 0 }}
                      animate={{ height: `${Math.max(h, 6)}%` }}
                      transition={{ duration: 0.5, delay: i * 0.02 }}
                      className="flex-1 bg-[#2cc4f5]/40 rounded-t-sm hover:bg-[#2cc4f5]/70 transition-colors cursor-pointer"
                      title={`${d.date}: ${d.stages_recorded} stages`}
                    />
                  );
                })}
              </div>
            ) : (
              <div className="h-20 flex items-center justify-center text-slate-300 text-xs font-mono">
                En attente d'activite...
              </div>
            )}
          </GlassCard>

          <GlassCard className="p-6" delay={0.24} data-testid="widget-live">
            <p className="font-mono text-[10px] text-slate-400 uppercase tracking-widest mb-4">
              Derniere Activite
            </p>
            {live?.last_activity ? (
              <div className="bg-slate-50/50 rounded-xl p-4 border border-slate-100">
                <div className="flex items-center gap-3">
                  <div
                    className="w-9 h-9 rounded-xl flex items-center justify-center text-xs"
                    style={{
                      backgroundColor: (STAGE_COLORS[live.last_activity.stage] || '#2cc4f5') + '15',
                      color: STAGE_COLORS[live.last_activity.stage] || '#2cc4f5'
                    }}
                  >
                    <i className={`fas ${STAGE_ICONS[live.last_activity.stage] || 'fa-circle'}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-slate-700">{live.last_activity.stage}</div>
                    <div className="text-[10px] text-slate-400 font-mono truncate">{live.last_activity.frek_id}</div>
                  </div>
                  <div className="text-[10px] text-slate-300 font-mono">
                    {live.last_activity.timestamp?.slice(11, 19)}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-slate-300 text-xs font-mono">En attente...</div>
            )}
          </GlassCard>
        </div>

        {/* FREK Notary — Notaire Culturel Tech */}
        <GlassCard className="p-6" delay={0.28} data-testid="widget-notary">
          <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-[#f7931a]/10 text-[#f7931a] border border-[#f7931a]/30">
                <span className="font-bold text-base">₿</span>
              </div>
              <div>
                <p className="font-mono text-[10px] text-slate-400 uppercase tracking-widest">
                  Notaire Culturel Tech
                </p>
                <p className="text-sm font-medium text-slate-700">
                  FREK-Chain · Bitcoin (OpenTimestamps)
                </p>
              </div>
            </div>
            <span
              data-testid="notary-integrity-badge"
              className={`px-2.5 py-1 rounded-full font-mono text-[10px] uppercase tracking-wider ${
                notary?.integrity_ok ?? true
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                  : 'bg-red-50 text-red-700 border border-red-200'
              }`}
            >
              {notary?.integrity_ok ?? true ? 'Inviolable' : 'COMPROMISE'}
            </span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-slate-50/50 rounded-xl p-3 border border-slate-100">
              <div className="font-mono text-[9px] text-slate-400 uppercase tracking-wider mb-1">
                Hauteur chaîne
              </div>
              <div data-testid="notary-height" className="text-xl font-semibold text-slate-800">
                {notary?.height ?? 0}
              </div>
            </div>
            <div className="bg-slate-50/50 rounded-xl p-3 border border-slate-100">
              <div className="font-mono text-[9px] text-slate-400 uppercase tracking-wider mb-1">
                Ancrés OTS
              </div>
              <div data-testid="notary-anchored" className="text-xl font-semibold text-slate-800">
                {notary?.total_anchored ?? 0}
              </div>
            </div>
            <div className="bg-slate-50/50 rounded-xl p-3 border border-slate-100">
              <div className="font-mono text-[9px] text-slate-400 uppercase tracking-wider mb-1">
                Confirmés BTC
              </div>
              <div data-testid="notary-btc-confirmed" className="text-xl font-semibold text-[#f7931a]">
                {notary?.total_btc_confirmed ?? 0}
              </div>
            </div>
            <div className="bg-slate-50/50 rounded-xl p-3 border border-slate-100">
              <div className="font-mono text-[9px] text-slate-400 uppercase tracking-wider mb-1">
                En attente BTC
              </div>
              <div data-testid="notary-pending" className="text-xl font-semibold text-slate-700">
                {notary?.pending_anchors ?? 0}
              </div>
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-100">
            <div className="font-mono text-[9px] text-slate-400 uppercase tracking-wider mb-1">
              Last block-hash
            </div>
            <div className="font-mono text-[10px] text-slate-500 break-all">
              {notary?.last_block_hash || '0'.repeat(64)}
            </div>
          </div>
        </GlassCard>

        {/* Footer */}
        <div className="text-center pt-4 pb-2">
          <p className="font-mono text-[10px] text-slate-300 tracking-widest uppercase">
            FREK v2.0 — Fichier de Referencement et d'Empreinte Kulturelle
          </p>
        </div>
      </main>
    </div>
  );
}
