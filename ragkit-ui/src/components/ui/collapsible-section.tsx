import { useState } from 'react';
import { cn } from '@/utils/cn';

interface CollapsibleSectionProps {
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}

export function CollapsibleSection({ title, defaultOpen = false, children }: CollapsibleSectionProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="rounded-2xl border border-slate-200 bg-white/70">
      <button
        type="button"
        onClick={() => setOpen((current) => !current)}
        className="flex w-full items-center justify-between px-4 py-3 text-sm font-semibold text-ink"
      >
        <span>{title}</span>
        <span className={cn('transition-transform', open ? 'rotate-180' : 'rotate-0')}>▾</span>
      </button>
      <div className={cn('overflow-hidden px-4 transition-all', open ? 'pb-4' : 'max-h-0')}>
        {open ? <div className="space-y-4">{children}</div> : null}
      </div>
    </div>
  );
}
