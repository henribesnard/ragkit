
import { useMemo, useState } from 'react';
import { ThumbsDown, ThumbsUp } from 'lucide-react';
import { cn } from '@/utils/cn';
import { submitFeedback } from '@/api/feedback';
import { CitationModal } from './CitationModal';

interface SourceItem {
  label: string;
  snippet?: string;
  score?: number;
}

interface RawSource {
  filename?: string;
  source?: string;
  source_name?: string;
  chunk?: string;
  snippet?: string;
  score?: number;
  [key: string]: any;
}

interface ChatMessageProps {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: Array<string | RawSource>;
  isStreaming?: boolean;
}

const normalizeSources = (sources?: Array<string | RawSource>): SourceItem[] => {
  if (!sources) {
    return [];
  }
  return sources.map((source, index) => {
    if (typeof source === 'string') {
      return { label: source };
    }
    const label =
      source.filename || source.source || source.source_name || source.path || `Source ${index + 1}`;
    const rawScore = source.score;
    const parsedScore =
      typeof rawScore === 'number' ? rawScore : rawScore !== undefined ? Number(rawScore) : undefined;
    return {
      label,
      snippet: source.chunk || source.snippet,
      score: Number.isFinite(parsedScore) ? parsedScore : undefined,
    };
  });
};

export function ChatMessage({ id, role, content, sources, isStreaming }: ChatMessageProps) {
  const [expandedCitation, setExpandedCitation] = useState<number | null>(null);
  const [feedback, setFeedback] = useState<'up' | 'down' | null>(null);
  const normalizedSources = useMemo(() => normalizeSources(sources), [sources]);

  const handleFeedback = async (rating: 'up' | 'down') => {
    setFeedback(rating);
    try {
      await submitFeedback({
        message_id: id,
        rating,
        metadata: {
          sources: normalizedSources.map((source) => source.label),
        },
      });
    } catch {
      // Ignore feedback errors to keep UI responsive.
    }
  };

  const renderContent = () => {
    const parts = content.split(/(\[\d+\])/g).filter(Boolean);
    return parts.map((part, index) => {
      const match = part.match(/\[(\d+)\]/);
      if (!match) {
        return <span key={`${part}-${index}`}>{part}</span>;
      }
      const citationIndex = Number(match[1]) - 1;
      const citation = normalizedSources[citationIndex];
      if (!citation) {
        return <span key={`${part}-${index}`}>{part}</span>;
      }
      return (
        <button
          key={`${part}-${index}`}
          type="button"
          onClick={() => setExpandedCitation(citationIndex)}
          className="mx-1 inline-flex rounded-full bg-accent/10 px-2 py-0.5 text-xs font-semibold text-accent hover:bg-accent/20"
        >
          {part}
        </button>
      );
    });
  };

  return (
    <div
      className={cn(
        'rounded-3xl px-5 py-4 text-sm shadow-soft',
        role === 'user'
          ? 'bg-accent text-white ml-auto max-w-[70%]'
          : 'bg-white/80 text-ink max-w-[80%]'
      )}
    >
      <p>
        {renderContent()}
        {isStreaming ? <span className="ml-1 animate-pulse">|</span> : null}
      </p>
      {normalizedSources.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2 text-xs text-muted">
          {normalizedSources.map((source, idx) => (
            <button
              key={source.label + idx}
              type="button"
              onClick={() => setExpandedCitation(idx)}
              className="rounded-full bg-canvas px-3 py-1 text-xs text-ink hover:bg-white"
            >
              {source.label}
            </button>
          ))}
        </div>
      )}
      {role === 'assistant' ? (
        <div className="mt-4 flex items-center gap-2 text-xs">
          <button
            type="button"
            onClick={() => handleFeedback('up')}
            className={cn(
              'flex items-center gap-1 rounded-full border border-transparent px-3 py-1',
              feedback === 'up' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'
            )}
          >
            <ThumbsUp size={14} />
            Helpful
          </button>
          <button
            type="button"
            onClick={() => handleFeedback('down')}
            className={cn(
              'flex items-center gap-1 rounded-full border border-transparent px-3 py-1',
              feedback === 'down' ? 'bg-rose-100 text-rose-700' : 'bg-slate-100 text-slate-600'
            )}
          >
            <ThumbsDown size={14} />
            Needs work
          </button>
        </div>
      ) : null}

      {expandedCitation !== null ? (
        <CitationModal
          source={normalizedSources[expandedCitation] ?? null}
          onClose={() => setExpandedCitation(null)}
        />
      ) : null}
    </div>
  );
}
