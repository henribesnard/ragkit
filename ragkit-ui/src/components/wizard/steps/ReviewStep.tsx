import { useTranslation } from 'react-i18next';

interface WizardStepProps {
  config: Record<string, any>;
}

export function ReviewStep({ config }: WizardStepProps) {
  const { t } = useTranslation();
  const project = config.project || {};
  const ingestion = config.ingestion || {};
  const source = (ingestion.sources || [])[0] || {};
  const chunking = ingestion.chunking || {};
  const embedding = config.embedding || {};
  const documentModel = embedding.document_model || {};
  const llm = config.llm || {};
  const primary = llm.primary || {};
  const retrieval = config.retrieval || {};

  const chunkSummary =
    chunking.strategy === 'semantic'
      ? t('wizard.review.chunking.semantic', {
          min: chunking.semantic?.min_chunk_size || 0,
          max: chunking.semantic?.max_chunk_size || 0,
        })
      : t('wizard.review.chunking.fixed', {
          size: chunking.fixed?.chunk_size || 0,
          overlap: chunking.fixed?.chunk_overlap || 0,
        });

  const environmentLabel = t(`common.environments.${project.environment || 'development'}`);

  return (
    <div className="space-y-4">
      <p className="text-sm font-semibold">{t('wizard.review.title')}</p>
      <div className="rounded-2xl border border-slate-200 bg-white/70 p-4 text-sm text-ink">
        <div className="space-y-3">
          <div>
            <p className="font-semibold">{t('wizard.review.projectTitle')}</p>
            <p className="text-xs text-muted">
              {project.name || t('wizard.review.unnamed')} · {environmentLabel}
            </p>
          </div>
          <div>
            <p className="font-semibold">{t('wizard.review.ingestionTitle')}</p>
            <p className="text-xs text-muted">
              {t('wizard.review.sourceLabel', {
                path: source.path || './data/documents',
                patterns: (source.patterns || []).join(', ') || '*.pdf, *.md, *.txt',
              })}
            </p>
            <p className="text-xs text-muted">{t('wizard.review.chunkingLabel', { summary: chunkSummary })}</p>
          </div>
          <div>
            <p className="font-semibold">{t('wizard.review.embeddingTitle')}</p>
            <p className="text-xs text-muted">
              {t('wizard.review.embeddingSummary', {
                provider: documentModel.provider || 'openai',
                model: documentModel.model || 'text-embedding-3-small',
              })}
            </p>
          </div>
          <div>
            <p className="font-semibold">{t('wizard.review.llmTitle')}</p>
            <p className="text-xs text-muted">
              {t('wizard.review.llmSummary', {
                provider: primary.provider || 'openai',
                model: primary.model || 'gpt-4o-mini',
              })}
            </p>
          </div>
          <div>
            <p className="font-semibold">{t('wizard.review.retrievalTitle')}</p>
            <p className="text-xs text-muted">
              {t('wizard.review.retrievalSummary', {
                architecture: retrieval.architecture || 'semantic',
                topK: retrieval.semantic?.top_k || 10,
              })}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
