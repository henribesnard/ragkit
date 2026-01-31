import { CollapsibleSection } from '@/components/ui/collapsible-section';
import { FieldLabel } from '@/components/ui/field-label';
import { NumberInput } from '@/components/ui/number-input';
import { Select } from '@/components/ui/select';
import { SliderInput } from '@/components/ui/slider-input';
import { ToggleSwitch } from '@/components/ui/toggle-switch';

interface WizardStepProps {
  config: Record<string, any>;
  onChange: (config: Record<string, any>) => void;
}

export function RetrievalStep({ config, onChange }: WizardStepProps) {
  const retrieval = config.retrieval || {};
  const semantic = retrieval.semantic || {};
  const lexical = retrieval.lexical || {};
  const rerank = retrieval.rerank || {};
  const context = retrieval.context || {};
  const dedup = context.deduplication || {};
  const lexicalParams = lexical.params || {};

  const updateRetrieval = (nextRetrieval: any) => {
    onChange({ ...config, retrieval: nextRetrieval });
  };

  const isSemantic = ['semantic', 'hybrid', 'hybrid_rerank'].includes(retrieval.architecture || 'semantic');
  const isLexical = ['lexical', 'hybrid', 'hybrid_rerank'].includes(retrieval.architecture || 'semantic');
  const isHybrid = ['hybrid', 'hybrid_rerank'].includes(retrieval.architecture || 'semantic');
  const isRerank = retrieval.architecture === 'hybrid_rerank';

  return (
    <div className="space-y-6">
      <div>
        <FieldLabel label="Architecture" help="Choix de la strategie de recherche." />
        <Select
          value={retrieval.architecture || 'semantic'}
          onChange={(event) => updateRetrieval({ ...retrieval, architecture: event.target.value })}
        >
          <option value="semantic">Semantic</option>
          <option value="lexical">Lexical</option>
          <option value="hybrid">Hybrid</option>
          <option value="hybrid_rerank">Hybrid + Rerank</option>
        </Select>
      </div>

      {isSemantic ? (
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-ink">Semantic</h3>
          {isHybrid ? (
            <div>
              <FieldLabel label="Weight" help="Poids de la recherche semantique." />
              <SliderInput
                value={semantic.weight ?? 0.5}
                onChange={(value) => updateRetrieval({ ...retrieval, semantic: { ...semantic, weight: value } })}
                min={0}
                max={1}
                step={0.05}
              />
            </div>
          ) : null}
          <div>
            <FieldLabel label="Top K" help="Nombre de resultats a retourner." />
            <NumberInput
              value={semantic.top_k ?? 10}
              min={1}
              max={100}
              step={1}
              onChange={(value) => updateRetrieval({ ...retrieval, semantic: { ...semantic, top_k: value ?? 10 } })}
            />
          </div>
          <div>
            <FieldLabel label="Similarity threshold" help="Score minimum de similarite." />
            <SliderInput
              value={semantic.similarity_threshold ?? 0}
              onChange={(value) =>
                updateRetrieval({ ...retrieval, semantic: { ...semantic, similarity_threshold: value } })
              }
              min={0}
              max={1}
              step={0.05}
            />
          </div>
        </div>
      ) : null}

      {isLexical ? (
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-ink">Lexical</h3>
          {isHybrid ? (
            <div>
              <FieldLabel label="Weight" help="Poids de la recherche lexicale." />
              <SliderInput
                value={lexical.weight ?? 0.5}
                onChange={(value) => updateRetrieval({ ...retrieval, lexical: { ...lexical, weight: value } })}
                min={0}
                max={1}
                step={0.05}
              />
            </div>
          ) : null}
          <div>
            <FieldLabel label="Top K" help="Nombre de resultats a retourner." />
            <NumberInput
              value={lexical.top_k ?? 10}
              min={1}
              max={100}
              step={1}
              onChange={(value) => updateRetrieval({ ...retrieval, lexical: { ...lexical, top_k: value ?? 10 } })}
            />
          </div>
          <div>
            <FieldLabel label="Algorithm" help="Algorithme lexical." />
            <Select
              value={lexical.algorithm || 'bm25'}
              onChange={(event) => updateRetrieval({ ...retrieval, lexical: { ...lexical, algorithm: event.target.value } })}
            >
              <option value="bm25">BM25</option>
              <option value="bm25+">BM25+</option>
            </Select>
          </div>
          <CollapsibleSection title="BM25 Parameters">
            <div>
              <FieldLabel label="k1" help="Saturation de la frequence des termes." />
              <SliderInput
                value={lexicalParams.k1 ?? 1.5}
                onChange={(value) =>
                  updateRetrieval({ ...retrieval, lexical: { ...lexical, params: { ...lexicalParams, k1: value } } })
                }
                min={0}
                max={3}
                step={0.05}
              />
            </div>
            <div>
              <FieldLabel label="b" help="Normalisation par longueur de document." />
              <SliderInput
                value={lexicalParams.b ?? 0.75}
                onChange={(value) =>
                  updateRetrieval({ ...retrieval, lexical: { ...lexical, params: { ...lexicalParams, b: value } } })
                }
                min={0}
                max={1}
                step={0.05}
              />
            </div>
          </CollapsibleSection>
        </div>
      ) : null}

      {isRerank ? (
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-ink">Reranking</h3>
          <div>
            <FieldLabel label="Enabled" help="Active le reranking." />
            <ToggleSwitch
              checked={rerank.enabled ?? false}
              onChange={(checked) => updateRetrieval({ ...retrieval, rerank: { ...rerank, enabled: checked } })}
            />
          </div>
          <div>
            <FieldLabel label="Top N" help="Nombre de resultats gardes apres reranking." />
            <NumberInput
              value={rerank.top_n ?? 5}
              min={1}
              max={50}
              step={1}
              onChange={(value) => updateRetrieval({ ...retrieval, rerank: { ...rerank, top_n: value ?? 5 } })}
            />
          </div>
        </div>
      ) : null}

      <CollapsibleSection title="Context">
        <div>
          <FieldLabel label="Max chunks" help="Nombre maximum de chunks envoyes au LLM." />
          <NumberInput
            value={context.max_chunks ?? 10}
            min={1}
            max={20}
            step={1}
            onChange={(value) => updateRetrieval({ ...retrieval, context: { ...context, max_chunks: value ?? 10 } })}
          />
        </div>
        <div>
          <FieldLabel label="Max tokens" help="Limite de tokens pour le contexte." />
          <NumberInput
            value={context.max_tokens ?? 2000}
            min={100}
            max={16000}
            step={100}
            onChange={(value) => updateRetrieval({ ...retrieval, context: { ...context, max_tokens: value ?? 2000 } })}
          />
        </div>
        <div>
          <FieldLabel label="Deduplication" help="Supprimer les chunks trop similaires." />
          <ToggleSwitch
            checked={dedup.enabled ?? true}
            onChange={(checked) =>
              updateRetrieval({
                ...retrieval,
                context: { ...context, deduplication: { ...dedup, enabled: checked } },
              })
            }
          />
        </div>
      </CollapsibleSection>
    </div>
  );
}
