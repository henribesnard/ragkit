import { useNavigate } from 'react-router-dom';
import { useAppStore } from '@/stores/appStore';
import { Menu } from 'lucide-react';

export function Header() {
  const navigate = useNavigate();
  const toggleSidebar = useAppStore((s) => s.toggleSidebar);

  return (
    <header className="flex items-center justify-between border-b border-white/40 bg-white/70 px-8 py-6 backdrop-blur-xl">
      <div className="flex items-center gap-4">
        <button
          onClick={toggleSidebar}
          className="rounded-xl p-2 text-muted hover:bg-white/80 lg:hidden"
          aria-label="Toggle sidebar"
        >
          <Menu size={20} />
        </button>
        <div>
          <p className="text-xs uppercase tracking-[0.25em] text-muted">Overview</p>
          <h2 className="text-2xl font-display">RAG system heartbeat</h2>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <span className="rounded-full bg-accent/10 px-3 py-1 text-xs font-semibold text-accent">
          live
        </span>
        <button
          onClick={() => navigate('/ingestion')}
          className="rounded-full bg-accent px-4 py-2 text-sm font-semibold text-white shadow-soft"
        >
          New Run
        </button>
      </div>
    </header>
  );
}
