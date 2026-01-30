import { cn } from '@/utils/cn';

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
}

export function ChatMessage({ role, content, sources }: ChatMessageProps) {
  return (
    <div
      className={cn(
        'rounded-3xl px-5 py-4 text-sm shadow-soft',
        role === 'user'
          ? 'bg-accent text-white ml-auto max-w-[70%]'
          : 'bg-white/80 text-ink max-w-[80%]'
      )}
    >
      <p>{content}</p>
      {sources && sources.length > 0 && (
        <div className="mt-3 text-xs text-muted">
          <p className="font-semibold">Sources</p>
          <ul className="list-disc pl-4">
            {sources.map((source) => (
              <li key={source}>{source}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
