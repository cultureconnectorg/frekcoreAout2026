/**
 * CC2026 Monitor Operationnel — Dashboard Luciole
 * Charte: #0C0818 (fond) / #C9A84C (or) / #3B0764 (accent violet)
 */
import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';

const API_URL = import.meta.env.VITE_BACKEND_URL || '';

const STAGES = ['GENESIS', 'WORKSHOP', 'METAMORPHOSE', 'EMISSION', 'LEGACY'];
const STAGE_COLORS = {
  GENESIS: '#C9A84C',
  WORKSHOP: '#3B82F6',
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

function formatNumber(n) {
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k';
  return n.toLocaleString('fr-FR');
}

function PulseIndicator({ active }) {
  return (
    <span className="relative flex h-2.5 w-2.5">
      {active && (
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
      )}
      <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${active ? 'bg-green-400' : 'bg-red-400'}`} />
    </span>
  );
}

function ProgressRing({ percentage, size = 120, strokeWidth = 8 }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percentage / 100) * circumference;

  return (
    <svg width={size} height={size} className="transform -rotate-90">
      <circle cx={size/2} cy={size/2} r={radius} fill="none" stroke="#1e1b2e" strokeWidth={strokeWidth} />
      <motion.circle
        cx={size/2} cy={size/2} r={radius} fill="none"
        stroke="url(#goldGradient)" strokeWidth={strokeWidth} strokeLinecap="round"
        initial={{ strokeDashoffset: circumference }}
        animate={{ strokeDashoffset: offset }}
        transition={{ duration: 1.5, ease: 'easeOut' }}
        strokeDasharray={circumference}
      />
      <defs>
        <linearGradient id="goldGradient" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#C9A84C" />
          <stop offset="100%" stopColor="#F5E6A3" />
        </linearGradient>
      </defs>
    </svg>
  );
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [live, setLive] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  const fetchDashboard = useCallback(async () => {
    try {
      const resp = await fetch(`${API_URL}/api/v1/dashboard/cc2026`);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const d = await resp.json();
      setData(d);
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchLive = useCallback(async () => {
    try {
      const resp = await fetch(`${API_URL}/api/v1/dashboard/cc2026/live`);
      if (!resp.ok) return;
      const d = await resp.json();
      setLive(d);
      setLastUpdate(new Date());
    } catch {}
  }, []);

  useEffect(() => {
    fetchDashboard();
    fetchLive();
    const interval = setInterval(fetchLive, 5000);
    return () => clearInterval(interval);
  }, [fetchDashboard, fetchLive]);

  const metrics = data?.metrics || {};
  const total = live?.total ?? metrics.total_identities ?? 0;
  const active = live?.active ?? metrics.active_identities ?? 0;
  const pct = live?.percentage ?? metrics.progression_percent ?? 0;
  const funnel = data?.luciole_funnel || [];
  const timeline = data?.timeline_30d || [];
  const clientsActivity = data?.clients_activity || {};

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0C0818] flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          className="w-12 h-12 border-2 border-[#C9A84C] border-t-transparent rounded-full"
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0C0818] text-white font-sans" data-testid="dashboard-cc2026">
      {/* Header */}
      <header className="border-b border-[#3B0764]/50 bg-[#0C0818]/95 backdrop-blur-md sticky top-0 z-50" data-testid="dashboard-header">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/" className="text-[#C9A84C] hover:text-[#F5E6A3] transition-colors">
              <i className="fas fa-arrow-left mr-2" />
              FREK
            </Link>
            <div className="h-6 w-px bg-[#3B0764]" />
            <h1 className="text-lg font-bold text-[#C9A84C] tracking-wide">CC2026 : Monitor</h1>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-[#161122] rounded-full border border-[#3B0764]/40 text-xs" data-testid="system-status">
              <PulseIndicator active={!error} />
              <span className="text-gray-400">FREK v1</span>
            </div>
            {lastUpdate && (
              <span className="text-xs text-gray-600">
                {lastUpdate.toLocaleTimeString('fr-FR')}
              </span>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {error && (
          <div className="bg-red-900/20 border border-red-500/30 rounded-lg px-4 py-3 text-red-300 text-sm" data-testid="error-banner">
            <i className="fas fa-exclamation-triangle mr-2" />{error}
          </div>
        )}

        {/* --- ROW 1: Metrics principales --- */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {/* Progression circulaire */}
          <motion.div
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            className="md:col-span-2 bg-[#161122] p-8 rounded-2xl border border-[#C9A84C]/20 shadow-2xl shadow-[#C9A84C]/5 flex items-center gap-8"
            data-testid="widget-progression"
          >
            <div className="relative">
              <ProgressRing percentage={pct} size={140} strokeWidth={10} />
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-3xl font-black text-[#C9A84C]">{pct}%</span>
                <span className="text-[10px] text-gray-500 uppercase tracking-wider">complété</span>
              </div>
            </div>
            <div className="flex-1">
              <h3 className="text-gray-400 text-xs uppercase tracking-widest mb-1">Objectif 40k IDs</h3>
              <div className="text-5xl font-black text-white" data-testid="total-identities">
                {total.toLocaleString('fr-FR')}
              </div>
              <div className="mt-3 w-full bg-[#1e1b2e] h-1.5 rounded-full overflow-hidden">
                <motion.div
                  className="h-full rounded-full bg-gradient-to-r from-[#C9A84C] to-[#F5E6A3]"
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(pct, 100)}%` }}
                  transition={{ duration: 1.2, ease: 'easeOut' }}
                />
              </div>
              <p className="text-xs mt-2 text-gray-500">
                {(40000 - total).toLocaleString('fr-FR')} restants
              </p>
            </div>
          </motion.div>

          {/* Actifs */}
          <motion.div
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
            className="bg-[#161122] p-6 rounded-2xl border border-green-500/20 shadow-xl"
            data-testid="widget-active"
          >
            <h3 className="text-gray-400 text-xs uppercase tracking-widest mb-3">Identités Actives</h3>
            <div className="text-4xl font-black text-green-400">{active.toLocaleString('fr-FR')}</div>
            <div className="mt-3 flex items-center gap-2 text-xs text-green-400/60">
              <PulseIndicator active />
              <span>Scanné physiquement</span>
            </div>
          </motion.div>

          {/* Clients */}
          <motion.div
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}
            className="bg-[#161122] p-6 rounded-2xl border border-blue-500/20 shadow-xl"
            data-testid="widget-clients"
          >
            <h3 className="text-gray-400 text-xs uppercase tracking-widest mb-3">Clients API</h3>
            <div className="text-4xl font-black text-blue-400">{Object.keys(clientsActivity).length}</div>
            <div className="mt-3 space-y-1">
              {Object.entries(clientsActivity).slice(0, 3).map(([id, count]) => (
                <div key={id} className="flex justify-between text-xs text-gray-500">
                  <span className="truncate mr-2">{id}</span>
                  <span className="text-gray-400">{count}</span>
                </div>
              ))}
            </div>
          </motion.div>
        </div>

        {/* --- ROW 2: Funnel Luciole --- */}
        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
          className="bg-[#161122] p-8 rounded-2xl border border-[#3B0764]/30 shadow-xl"
          data-testid="widget-funnel"
        >
          <h3 className="text-gray-400 text-xs uppercase tracking-widest mb-6">
            <i className="fas fa-fire mr-2 text-[#C9A84C]" />
            Funnel Luciole — 5 Stages
          </h3>
          <div className="grid grid-cols-5 gap-4">
            {STAGES.map((stage, i) => {
              const count = funnel.find(f => f.stage === stage)?.count || 0;
              const maxCount = Math.max(...funnel.map(f => f.count), 1);
              const pctBar = (count / maxCount) * 100;

              return (
                <motion.div
                  key={stage}
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 + i * 0.08 }}
                  className="text-center"
                >
                  <div className="h-32 flex flex-col justify-end mb-3">
                    <motion.div
                      className="rounded-t-lg mx-auto w-full max-w-[60px]"
                      style={{ backgroundColor: STAGE_COLORS[stage] + '30' }}
                      initial={{ height: 0 }}
                      animate={{ height: `${Math.max(pctBar, 8)}%` }}
                      transition={{ duration: 0.8, delay: 0.4 + i * 0.1 }}
                    >
                      <div
                        className="rounded-t-lg w-full h-full"
                        style={{ backgroundColor: STAGE_COLORS[stage], opacity: 0.8 }}
                      />
                    </motion.div>
                  </div>
                  <div className="text-2xl font-bold" style={{ color: STAGE_COLORS[stage] }}>
                    {count}
                  </div>
                  <div className="text-[10px] text-gray-500 uppercase tracking-wider mt-1 flex items-center justify-center gap-1">
                    <i className={`fas ${STAGE_ICONS[stage]} text-[8px]`} style={{ color: STAGE_COLORS[stage] }} />
                    {stage}
                  </div>
                </motion.div>
              );
            })}
          </div>
          <div className="mt-6 flex items-center justify-center gap-2">
            {STAGES.map((stage, i) => (
              <div key={stage} className="flex items-center gap-1">
                {i > 0 && <i className="fas fa-chevron-right text-[8px] text-gray-700 mx-1" />}
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: STAGE_COLORS[stage] }} />
                <span className="text-[9px] text-gray-600">{i + 1}</span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* --- ROW 3: Timeline + Last Activity --- */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Timeline 30j */}
          <motion.div
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }}
            className="bg-[#161122] p-6 rounded-2xl border border-[#3B0764]/30 shadow-xl"
            data-testid="widget-timeline"
          >
            <h3 className="text-gray-400 text-xs uppercase tracking-widest mb-4">
              <i className="fas fa-chart-line mr-2 text-[#C9A84C]" />
              Activité 30 jours
            </h3>
            {timeline.length > 0 ? (
              <div className="flex items-end gap-1 h-24">
                {timeline.map((d, i) => {
                  const maxVal = Math.max(...timeline.map(t => t.stages_recorded), 1);
                  const h = (d.stages_recorded / maxVal) * 100;
                  return (
                    <motion.div
                      key={d.date}
                      initial={{ height: 0 }}
                      animate={{ height: `${Math.max(h, 4)}%` }}
                      transition={{ duration: 0.5, delay: i * 0.02 }}
                      className="flex-1 bg-[#C9A84C]/60 rounded-t hover:bg-[#C9A84C] transition-colors cursor-pointer"
                      title={`${d.date}: ${d.stages_recorded} stages`}
                    />
                  );
                })}
              </div>
            ) : (
              <div className="h-24 flex items-center justify-center text-gray-600 text-sm">
                Aucune activité enregistrée
              </div>
            )}
          </motion.div>

          {/* Live Feed */}
          <motion.div
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
            className="bg-[#161122] p-6 rounded-2xl border border-[#3B0764]/30 shadow-xl"
            data-testid="widget-live"
          >
            <h3 className="text-gray-400 text-xs uppercase tracking-widest mb-4">
              <i className="fas fa-stream mr-2 text-green-400" />
              Dernière Activité
            </h3>
            {live?.last_activity ? (
              <div className="space-y-3">
                <div className="flex items-center gap-3 bg-[#0C0818] rounded-lg p-3 border border-[#3B0764]/20">
                  <div
                    className="w-8 h-8 rounded-lg flex items-center justify-center text-xs"
                    style={{ backgroundColor: STAGE_COLORS[live.last_activity.stage] + '20', color: STAGE_COLORS[live.last_activity.stage] }}
                  >
                    <i className={`fas ${STAGE_ICONS[live.last_activity.stage] || 'fa-circle'}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-gray-300">{live.last_activity.stage}</div>
                    <div className="text-xs text-gray-600 truncate">{live.last_activity.frek_id}</div>
                  </div>
                  <div className="text-[10px] text-gray-500">
                    {live.last_activity.timestamp?.slice(11, 19)}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-gray-600 text-sm">En attente d'activité...</div>
            )}
          </motion.div>
        </div>

        {/* Footer */}
        <div className="text-center text-xs text-gray-700 pt-4 pb-8">
          FREK v2.0.0 — Fichier de Référencement et d'Empreinte Kulturelle — frekcore.com
        </div>
      </main>
    </div>
  );
}
