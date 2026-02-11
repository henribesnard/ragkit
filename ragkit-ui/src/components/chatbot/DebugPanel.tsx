import { useTranslation } from 'react-i18next';

interface DebugPanelProps {
  lastMessage?: {
    debug?: {
      intent?: string;
      latency_ms?: number;
      chunks_retrieved?: number;
      needs_retrieval?: boolean;
      detected_language?: string;
      response_language?: string;
      streaming?: boolean;
    };
  };
  onClose?: () => void;
}

export function DebugPanel({ lastMessage, onClose }: DebugPanelProps) {
  const { t } = useTranslation();
  const debug = lastMessage?.debug;
  return (
    <div className="h-full border-l border-white/40 bg-white/70 p-6 backdrop-blur-xl">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">{t('chat.debug.title')}</h3>
        {onClose && (
          <button onClick={onClose} className="text-xs text-muted">
            {t('common.actions.close')}
          </button>
        )}
      </div>
      <div className="mt-6 space-y-3 text-xs text-muted">
        <p>{t('chat.debug.intent')}: {debug?.intent || '--'}</p>
        <p>{t('chat.debug.latency')}: {Math.round(debug?.latency_ms || 0)}ms</p>
        <p>{t('chat.debug.chunks')}: {debug?.chunks_retrieved ?? 0}</p>
        <p>{t('chat.debug.needsRetrieval')}: {debug?.needs_retrieval ? t('common.values.yes') : t('common.values.no')}</p>
        <p>
          {t('chat.debug.language')}: {debug?.detected_language || '--'} {'->'} {debug?.response_language || '--'}
        </p>
        {debug?.streaming !== undefined ? (
          <p>{t('chat.debug.streaming')}: {debug.streaming ? t('common.values.yes') : t('common.values.no')}</p>
        ) : null}
      </div>
    </div>
  );
}
