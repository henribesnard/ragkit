import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';

interface HelpTooltipProps {
  text: string;
}

export function HelpTooltip({ text }: HelpTooltipProps) {
  const { t } = useTranslation();
  const [show, setShow] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (!wrapperRef.current) {
        return;
      }
      if (!wrapperRef.current.contains(event.target as Node)) {
        setShow(false);
      }
    }
    if (show) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [show]);

  return (
    <div ref={wrapperRef} className="relative inline-flex">
      <button
        type="button"
        onMouseEnter={() => setShow(true)}
        onMouseLeave={() => setShow(false)}
        onClick={() => setShow((current) => !current)}
        className="ml-1.5 inline-flex h-4 w-4 items-center justify-center rounded-full bg-slate-200 text-[10px] font-bold text-slate-500 hover:bg-accent/20 hover:text-accent"
        aria-label={t('common.actions.help')}
      >
        ?
      </button>
      {show && (
        <div className="absolute left-6 top-0 z-50 w-64 rounded-xl border border-slate-200 bg-white p-3 text-xs text-slate-600 shadow-lg">
          {text}
        </div>
      )}
    </div>
  );
}
