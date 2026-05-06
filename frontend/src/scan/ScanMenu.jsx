/** Menu — 3 modes terrain + lien queue */
import { Link } from 'react-router-dom';

const MODES = [
  {
    to: '/scan/access',
    perm: 'scan_access',
    title: 'Accès',
    subtitle: 'Contrôle entrée / zones',
    color: '#2cc4f5',
    icon: '🚪',
    testid: 'mode-access',
  },
  {
    to: '/scan/cashless',
    perm: 'scan_cashless',
    title: 'Cashless',
    subtitle: 'Paiement jetons marchand',
    color: '#f7931a',
    icon: '₿',
    testid: 'mode-cashless',
  },
  {
    to: '/scan/emit',
    perm: 'emit_walkin',
    title: 'Émission',
    subtitle: 'Walk-in : créer FREK-ID',
    color: '#10B981',
    icon: '✦',
    testid: 'mode-emit',
  },
];

export default function ScanMenu({ staff }) {
  const perms = new Set(staff?.permissions || []);
  return (
    <div className="space-y-6" data-testid="scan-menu">
      <div className="text-center pt-2">
        <h1 className="font-mono text-xl uppercase tracking-widest text-white mb-1">Bonjour, {staff?.nom}</h1>
        <p className="font-mono text-[10px] text-white/40 tracking-wider uppercase">
          Rôle : {staff?.role} · Zones : {staff?.allowed_zones?.join(', ') || '—'}
        </p>
      </div>
      <div className="grid grid-cols-1 gap-3">
        {MODES.map((m) => {
          const enabled = perms.has(m.perm);
          return (
            <Link
              key={m.to}
              to={enabled ? m.to : '#'}
              data-testid={m.testid}
              data-enabled={enabled}
              onClick={(e) => { if (!enabled) e.preventDefault(); }}
              className={`flex items-center gap-4 p-5 rounded-2xl border transition ${
                enabled
                  ? 'bg-white/5 border-white/15 active:bg-white/10'
                  : 'bg-white/[0.02] border-white/5 opacity-40 cursor-not-allowed'
              }`}
              style={enabled ? { borderColor: `${m.color}40` } : undefined}
            >
              <div
                className="w-14 h-14 rounded-xl flex items-center justify-center text-2xl font-bold"
                style={{
                  backgroundColor: `${m.color}15`,
                  color: m.color,
                  borderWidth: '1px',
                  borderColor: `${m.color}40`,
                }}
              >
                {m.icon}
              </div>
              <div className="flex-1">
                <div className="font-mono text-base text-white uppercase tracking-wider">{m.title}</div>
                <div className="font-mono text-[11px] text-white/50">{m.subtitle}</div>
              </div>
              <div className="text-white/30 text-xl">→</div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
