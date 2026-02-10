import { X } from 'lucide-react';

interface CitationModalProps {
  source: {
    label: string;
    snippet?: string;
    score?: number;
  } | null;
  onClose: () => void;
}

export function CitationModal({ source, onClose }: CitationModalProps) {
  if (!source) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-6">
      <div className="relative w-full max-w-2xl rounded-3xl bg-white p-6 shadow-glow">
        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 rounded-full bg-slate-100 p-2 text-slate-600 hover:bg-slate-200"
        >
          <X size={16} />
        </button>
        <p className="text-xs uppercase tracking-[0.3em] text-muted">Citation</p>
        <h3 className="mt-2 text-lg font-display">{source.label}</h3>
        {source.score !== undefined ? (
          <p className="mt-1 text-xs text-muted">Score: {source.score.toFixed(2)}</p>
        ) : null}
        <div className="mt-4 rounded-2xl bg-canvas p-4 text-sm text-ink">
          {source.snippet || 'No snippet available for this citation yet.'}
        </div>
      </div>
    </div>
  );
}
