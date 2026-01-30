interface DebugPanelProps {
  lastMessage?: {
    debug?: {
      intent?: string;
      latency_ms?: number;
      chunks_retrieved?: number;
      needs_retrieval?: boolean;
    };
  };
  onClose?: () => void;
}

export function DebugPanel({ lastMessage, onClose }: DebugPanelProps) {
  const debug = lastMessage?.debug;
  return (
    <div className="h-full border-l border-white/40 bg-white/70 p-6 backdrop-blur-xl">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">Debug</h3>
        {onClose && (
          <button onClick={onClose} className="text-xs text-muted">
            Close
          </button>
        )}
      </div>
      <div className="mt-6 space-y-3 text-xs text-muted">
        <p>Intent: {debug?.intent || '--'}</p>
        <p>Latency: {Math.round(debug?.latency_ms || 0)}ms</p>
        <p>Chunks: {debug?.chunks_retrieved ?? 0}</p>
        <p>Needs retrieval: {debug?.needs_retrieval ? 'yes' : 'no'}</p>
      </div>
    </div>
  );
}
