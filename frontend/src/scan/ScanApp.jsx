/**
 * FREK Scanner — Shell PWA terrain.
 * Routes /scan, /scan/login, /scan/access, /scan/cashless, /scan/emit, /scan/queue
 */
import { useEffect, useState } from 'react';
import { Routes, Route, Navigate, Link, useNavigate, useLocation } from 'react-router-dom';
import {
  api, getStaff, getToken, setSession, clearSession, queueCount, flushQueue,
} from './lib';
import ScanLogin from './ScanLogin';
import ScanMenu from './ScanMenu';
import ScanAccess from './ScanAccess';
import ScanCashless from './ScanCashless';
import ScanEmit from './ScanEmit';
import ScanQueue from './ScanQueue';

function RequireAuth({ children }) {
  const tok = getToken();
  if (!tok) return <Navigate to="/scan/login" replace />;
  return children;
}

function ScanHeader({ pendingCount, online, staff, onLogout }) {
  return (
    <header className="sticky top-0 z-30 bg-[#0a0a0a]/95 backdrop-blur border-b border-white/10">
      <div className="px-4 py-3 flex items-center justify-between gap-3">
        <Link to="/scan" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-[#f7931a]/20 border border-[#f7931a]/40 flex items-center justify-center">
            <span className="text-[#f7931a] font-bold">₿</span>
          </div>
          <div className="leading-tight">
            <div className="font-mono text-[10px] text-[#f7931a] uppercase tracking-widest">FREK Scan</div>
            <div className="font-mono text-[9px] text-white/40 uppercase tracking-wider">CC2026</div>
          </div>
        </Link>
        <div className="flex items-center gap-2">
          <Link
            to="/scan/queue"
            data-testid="header-queue-link"
            className="relative px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-white/80 font-mono text-[10px] uppercase tracking-wider"
          >
            File {pendingCount > 0 && (
              <span data-testid="queue-badge" className="ml-1 px-1.5 py-0.5 rounded-full bg-[#f7931a] text-black text-[9px] font-bold">{pendingCount}</span>
            )}
          </Link>
          <span
            data-testid="online-status"
            className={`inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-full font-mono text-[10px] uppercase tracking-wider ${
              online ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30' : 'bg-red-500/15 text-red-300 border border-red-500/30'
            }`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${online ? 'bg-emerald-400' : 'bg-red-400'}`} />
            {online ? 'En ligne' : 'Hors ligne'}
          </span>
          {staff && (
            <button
              data-testid="logout-btn"
              onClick={onLogout}
              className="px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-white/70 font-mono text-[10px] uppercase tracking-wider"
              title={`${staff.agent_id} · ${staff.role}`}
            >
              {staff.agent_id}
            </button>
          )}
        </div>
      </div>
    </header>
  );
}

export default function ScanApp() {
  const navigate = useNavigate();
  const location = useLocation();
  const [staff, setStaff] = useState(getStaff());
  const [online, setOnline] = useState(navigator.onLine);
  const [pending, setPending] = useState(0);

  // Online listener + auto-flush queue when back online
  useEffect(() => {
    const goOnline = async () => {
      setOnline(true);
      try {
        const c = await queueCount();
        if (c > 0 && getToken()) {
          await flushQueue();
          setPending(await queueCount());
        }
      } catch {}
    };
    const goOffline = () => setOnline(false);
    window.addEventListener('online', goOnline);
    window.addEventListener('offline', goOffline);
    return () => {
      window.removeEventListener('online', goOnline);
      window.removeEventListener('offline', goOffline);
    };
  }, []);

  // Refresh pending count every 4s + on route change
  useEffect(() => {
    let alive = true;
    const tick = async () => {
      try {
        if (alive) setPending(await queueCount());
      } catch {}
    };
    tick();
    const i = setInterval(tick, 4000);
    return () => { alive = false; clearInterval(i); };
  }, [location.pathname]);

  // Refresh /me on mount if token present
  useEffect(() => {
    if (getToken() && !staff) {
      api.me().then((m) => { setSession(getToken(), m); setStaff(m); }).catch(() => {});
    }
  }, [staff]);

  const handleLogin = (token, info) => {
    setSession(token, info);
    setStaff(info);
    navigate('/scan');
  };

  const handleLogout = () => {
    clearSession();
    setStaff(null);
    navigate('/scan/login');
  };

  // PWA service worker registration
  useEffect(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/scan-sw.js', { scope: '/scan' }).catch(() => {});
    }
  }, []);

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white" data-testid="scan-app">
      <ScanHeader pendingCount={pending} online={online} staff={staff} onLogout={handleLogout} />
      <main className="px-4 py-5 max-w-xl mx-auto">
        <Routes>
          <Route path="login" element={<ScanLogin onLogin={handleLogin} />} />
          <Route path="" element={<RequireAuth><ScanMenu staff={staff} /></RequireAuth>} />
          <Route path="access" element={<RequireAuth><ScanAccess staff={staff} online={online} /></RequireAuth>} />
          <Route path="cashless" element={<RequireAuth><ScanCashless staff={staff} online={online} /></RequireAuth>} />
          <Route path="emit" element={<RequireAuth><ScanEmit staff={staff} online={online} /></RequireAuth>} />
          <Route path="queue" element={<RequireAuth><ScanQueue staff={staff} online={online} /></RequireAuth>} />
        </Routes>
      </main>
    </div>
  );
}
