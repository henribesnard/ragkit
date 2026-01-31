interface WizardStepProps {
  config: Record<string, any>;
}

export function ReviewStep({ config }: WizardStepProps) {
  const project = config.project || {};
  const ingestion = config.ingestion || {};
  const source = (ingestion.sources || [])[0] || {};
  const chunking = ingestion.chunking || {};
  const embedding = config.embedding || {};
  const documentModel = embedding.document_model || {};
  const llm = config.llm || {};
  const primary = llm.primary || {};
  const retrieval = config.retrieval || {};

  const chunkSummary = chunking.strategy === 'semantic'
    ? `semantic, min ${chunking.semantic?.min_chunk_size || 0}, max ${chunking.semantic?.max_chunk_size || 0}`
    : `fixed, ${chunking.fixed?.chunk_size || 0} chars, ${chunking.fixed?.chunk_overlap || 0} overlap`;

  return (
    <div className="space-y-4">
      <p className="text-sm font-semibold">Review configuration</p>
      <div className="rounded-2xl border border-slate-200 bg-white/70 p-4 text-sm text-ink">
        <div className="space-y-3">
          <div>
            <p className="font-semibold">Project</p>
            <p className="text-xs text-muted">{project.name || 'Unnamed'} · {project.environment || 'development'}</p>
          </div>
          <div>
            <p className="font-semibold">Ingestion</p>
            <p className="text-xs text-muted">
              Source: {source.path || './data/documents'} ({(source.patterns || []).join(', ') || '*.pdf, *.md, *.txt'})
            </p>
            <p className="text-xs text-muted">Chunking: {chunkSummary}</p>
          </div>
          <div>
            <p className="font-semibold">Embedding</p>
            <p className="text-xs text-muted">
              Provider: {documentModel.provider || 'openai'} · Model: {documentModel.model || 'text-embedding-3-small'}
            </p>
          </div>
          <div>
            <p className="font-semibold">LLM</p>
            <p className="text-xs text-muted">
              Primary: {primary.provider || 'openai'} · {primary.model || 'gpt-4o-mini'}
            </p>
          </div>
          <div>
            <p className="font-semibold">Retrieval</p>
            <p className="text-xs text-muted">
              Architecture: {retrieval.architecture || 'semantic'} · Top K: {retrieval.semantic?.top_k || 10}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
