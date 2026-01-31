import { NavLink } from 'react-router-dom';
import { LayoutGrid, Settings2, PlugZap, MessageCircle, FileStack, Activity } from 'lucide-react';
import { useStatus } from '@/hooks/useStatus';

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutGrid },
  { to: '/setup', label: 'Setup Wizard', icon: PlugZap },
  { to: '/config', label: 'Configuration', icon: Settings2 },
  { to: '/ingestion', label: 'Ingestion', icon: FileStack },
  { to: '/chatbot', label: 'Chatbot', icon: MessageCircle },
  { to: '/logs', label: 'Logs', icon: Activity },
];

export function Sidebar({ open = true }: { open?: boolean }) {
  const { data: status } = useStatus();
  return (
    <aside
      className={`shrink-0 border-r border-white/40 bg-white/70 backdrop-blur-xl transition-all ${
        open ? 'w-72' : 'w-0 overflow-hidden'
      }`}
    >
      <div className="px-6 py-8">
        <p className="text-xs uppercase tracking-[0.3em] text-muted">RAGKIT</p>
        <h1 className="mt-2 text-2xl font-display">Control Room</h1>
        {status?.setup_mode && (
          <span className="mt-3 inline-flex rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-800">
            Setup mode
          </span>
        )}
      </div>
      <nav className="flex flex-col gap-2 px-4">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition ${
                isActive
                  ? 'bg-accent text-white shadow-glow'
                  : 'text-ink/80 hover:bg-white/80'
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
