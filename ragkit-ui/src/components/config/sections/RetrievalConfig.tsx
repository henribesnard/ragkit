import { CollapsibleSection } from '@/components/ui/collapsible-section';
import { FieldLabel } from '@/components/ui/field-label';
import { Input } from '@/components/ui/input';
import { NumberInput } from '@/components/ui/number-input';
import { Select } from '@/components/ui/select';
import { SliderInput } from '@/components/ui/slider-input';
import { ToggleSwitch } from '@/components/ui/toggle-switch';

interface SectionProps {
  config: any;
  onChange: (value: any) => void;
}

export function RetrievalConfigSection({ config, onChange }: SectionProps) {
  const retrieval = config?.retrieval || {};
  const semantic = retrieval.semantic || {};
  const lexical = retrieval.lexical || {};
  const rerank = retrieval.rerank || {};
  const fusion = retrieval.fusion || {};
  const context = retrieval.context || {};
  const dedup = context.deduplication || {};
  const lexicalParams = lexical.params || {};
  const lexicalPre = lexical.preprocessing || {};

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
        <FieldLabel
          label="Architecture"
          help="Strategie de recherche. semantic : recherche par similarite vectorielle. lexical : recherche par mots-cles. hybrid : combine les deux. hybrid_rerank : hybrid + reranking."
        />
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
          <h3 className="text-sm font-semibold text-ink">Recherche Semantique</h3>
          <div>
            <FieldLabel label="Enabled" help="Active la recherche semantique." />
            <ToggleSwitch
              checked={semantic.enabled ?? true}
              onChange={(checked) =>
                updateRetrieval({ ...retrieval, semantic: { ...semantic, enabled: checked } })
              }
            />
          </div>
          {isHybrid ? (
            <div>
              <FieldLabel
                label="Weight"
                help="Poids de la recherche semantique dans le score final hybrid."
              />
              <SliderInput
                value={semantic.weight ?? 0.5}
                onChange={(value) =>
                  updateRetrieval({ ...retrieval, semantic: { ...semantic, weight: value } })
                }
                min={0}
                max={1}
                step={0.05}
              />
            </div>
          ) : null}
          <div>
            <FieldLabel label="Top K" help="Nombre de resultats a retourner par la recherche semantique." />
            <NumberInput
              value={semantic.top_k ?? 20}
              min={1}
              max={100}
              step={1}
              onChange={(value) =>
                updateRetrieval({ ...retrieval, semantic: { ...semantic, top_k: value ?? 20 } })
              }
            />
          </div>
          <div>
            <FieldLabel
              label="Similarity threshold"
              help="Score minimum de similarite pour qu'un resultat soit retenu."
            />
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
          <h3 className="text-sm font-semibold text-ink">Recherche Lexicale</h3>
          <div>
            <FieldLabel label="Enabled" help="Active la recherche lexicale." />
            <ToggleSwitch
              checked={lexical.enabled ?? false}
              onChange={(checked) =>
                updateRetrieval({ ...retrieval, lexical: { ...lexical, enabled: checked } })
              }
            />
          </div>
          {isHybrid ? (
            <div>
              <FieldLabel label="Weight" help="Poids de la recherche lexicale dans le score final hybrid." />
              <SliderInput
                value={lexical.weight ?? 0.5}
                onChange={(value) =>
                  updateRetrieval({ ...retrieval, lexical: { ...lexical, weight: value } })
                }
                min={0}
                max={1}
                step={0.05}
              />
            </div>
          ) : null}
          <div>
            <FieldLabel label="Top K" help="Nombre de resultats a retourner par la recherche lexicale." />
            <NumberInput
              value={lexical.top_k ?? 20}
              min={1}
              max={100}
              step={1}
              onChange={(value) =>
                updateRetrieval({ ...retrieval, lexical: { ...lexical, top_k: value ?? 20 } })
              }
            />
          </div>
          <div>
            <FieldLabel label="Algorithm" help="Algorithme de recherche lexical (BM25)." />
            <Select
              value={lexical.algorithm || 'bm25'}
              onChange={(event) =>
                updateRetrieval({ ...retrieval, lexical: { ...lexical, algorithm: event.target.value } })
              }
            >
              <option value="bm25">BM25</option>
              <option value="bm25+">BM25+</option>
            </Select>
          </div>

          <CollapsibleSection title="BM25 Parameters">
            <div>
              <FieldLabel label="k1" help="Controle la saturation de la frequence des termes." />
              <SliderInput
                value={lexicalParams.k1 ?? 1.5}
                onChange={(value) =>
                  updateRetrieval({
                    ...retrieval,
                    lexical: { ...lexical, params: { ...lexicalParams, k1: value } },
                  })
                }
                min={0}
                max={3}
                step={0.05}
              />
            </div>
            <div>
              <FieldLabel label="b" help="Controle la normalisation par longueur de document." />
              <SliderInput
                value={lexicalParams.b ?? 0.75}
                onChange={(value) =>
                  updateRetrieval({
                    ...retrieval,
                    lexical: { ...lexical, params: { ...lexicalParams, b: value } },
                  })
                }
                min={0}
                max={1}
                step={0.05}
              />
            </div>
          </CollapsibleSection>

          <CollapsibleSection title="Preprocessing">
            <div>
              <FieldLabel label="Lowercase" help="Convertir les textes en minuscules avant la recherche." />
              <ToggleSwitch
                checked={lexicalPre.lowercase ?? true}
                onChange={(checked) =>
                  updateRetrieval({
                    ...retrieval,
                    lexical: { ...lexical, preprocessing: { ...lexicalPre, lowercase: checked } },
                  })
                }
              />
            </div>
            <div>
              <FieldLabel label="Remove stopwords" help="Retirer les mots vides qui n'apportent pas de sens." />
              <ToggleSwitch
                checked={lexicalPre.remove_stopwords ?? true}
                onChange={(checked) =>
                  updateRetrieval({
                    ...retrieval,
                    lexical: { ...lexical, preprocessing: { ...lexicalPre, remove_stopwords: checked } },
                  })
                }
              />
            </div>
            <div>
              <FieldLabel label="Stopwords lang" help="Langue des mots vides." />
              <Select
                value={lexicalPre.stopwords_lang || 'auto'}
                onChange={(event) =>
                  updateRetrieval({
                    ...retrieval,
                    lexical: { ...lexical, preprocessing: { ...lexicalPre, stopwords_lang: event.target.value } },
                  })
                }
              >
                <option value="auto">Auto</option>
                <option value="french">French</option>
                <option value="english">English</option>
              </Select>
            </div>
            <div>
              <FieldLabel label="Stemming" help="Reduire les mots a leur racine." />
              <ToggleSwitch
                checked={lexicalPre.stemming ?? false}
                onChange={(checked) =>
                  updateRetrieval({
                    ...retrieval,
                    lexical: { ...lexical, preprocessing: { ...lexicalPre, stemming: checked } },
                  })
                }
              />
            </div>
          </CollapsibleSection>
        </div>
      ) : null}

      {isRerank ? (
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-ink">Reranking</h3>
          <div>
            <FieldLabel label="Enabled" help="Active le reranking pour raffiner les resultats." />
            <ToggleSwitch
              checked={rerank.enabled ?? false}
              onChange={(checked) => updateRetrieval({ ...retrieval, rerank: { ...rerank, enabled: checked } })}
            />
          </div>
          <div>
            <FieldLabel label="Provider" help="Service de reranking qui re-evalue la pertinence." />
            <Select
              value={rerank.provider || 'none'}
              onChange={(event) => updateRetrieval({ ...retrieval, rerank: { ...rerank, provider: event.target.value } })}
            >
              <option value="none">None</option>
              <option value="cohere">Cohere</option>
            </Select>
          </div>
          <div>
            <FieldLabel label="Model" help="Modele de reranking (ex: rerank-english-v3.0)." />
            <Input
              value={rerank.model || ''}
              onChange={(event) => updateRetrieval({ ...retrieval, rerank: { ...rerank, model: event.target.value } })}
            />
          </div>
          <div>
            <FieldLabel label="API key" help="Cle d'API pour le provider de reranking." />
            <Input
              type="password"
              placeholder="sk-..."
              value={rerank.api_key || ''}
              onChange={(event) => updateRetrieval({ ...retrieval, rerank: { ...rerank, api_key: event.target.value } })}
            />
          </div>
          <div>
            <FieldLabel label="Top N" help="Nombre de resultats a garder apres le reranking." />
            <NumberInput
              value={rerank.top_n ?? 5}
              min={1}
              max={50}
              step={1}
              onChange={(value) => updateRetrieval({ ...retrieval, rerank: { ...rerank, top_n: value ?? 5 } })}
            />
          </div>
          <div>
            <FieldLabel label="Candidates" help="Nombre de resultats envoyes au reranker." />
            <NumberInput
              value={rerank.candidates ?? 40}
              min={1}
              max={200}
              step={1}
              onChange={(value) => updateRetrieval({ ...retrieval, rerank: { ...rerank, candidates: value ?? 40 } })}
            />
          </div>
          <div>
            <FieldLabel label="Relevance threshold" help="Score minimum du reranker pour garder un resultat." />
            <SliderInput
              value={rerank.relevance_threshold ?? 0}
              onChange={(value) => updateRetrieval({ ...retrieval, rerank: { ...rerank, relevance_threshold: value } })}
              min={0}
              max={1}
              step={0.05}
            />
          </div>
        </div>
      ) : null}

      {isHybrid ? (
        <CollapsibleSection title="Fusion">
          <div>
            <FieldLabel label="Method" help="weighted_sum ou reciprocal_rank_fusion." />
            <Select
              value={fusion.method || 'weighted_sum'}
              onChange={(event) => updateRetrieval({ ...retrieval, fusion: { ...fusion, method: event.target.value } })}
            >
              <option value="weighted_sum">Weighted sum</option>
              <option value="reciprocal_rank_fusion">Reciprocal rank fusion</option>
            </Select>
          </div>
          <div>
            <FieldLabel label="Normalize scores" help="Normaliser les scores avant fusion." />
            <ToggleSwitch
              checked={fusion.normalize_scores ?? true}
              onChange={(checked) => updateRetrieval({ ...retrieval, fusion: { ...fusion, normalize_scores: checked } })}
            />
          </div>
          {fusion.method === 'reciprocal_rank_fusion' ? (
            <div>
              <FieldLabel label="RRF K" help="Parametre de la fusion RRF." />
              <NumberInput
                value={fusion.rrf_k ?? 60}
                min={1}
                max={200}
                step={1}
                onChange={(value) => updateRetrieval({ ...retrieval, fusion: { ...fusion, rrf_k: value ?? 60 } })}
              />
            </div>
          ) : null}
        </CollapsibleSection>
      ) : null}

      <CollapsibleSection title="Context">
        <div>
          <FieldLabel label="Max chunks" help="Nombre maximum de morceaux de contexte envoyes au LLM." />
          <NumberInput
            value={context.max_chunks ?? 10}
            min={1}
            max={20}
            step={1}
            onChange={(value) => updateRetrieval({ ...retrieval, context: { ...context, max_chunks: value ?? 10 } })}
          />
        </div>
        <div>
          <FieldLabel label="Max tokens" help="Limite de tokens du contexte injecte dans le prompt." />
          <NumberInput
            value={context.max_tokens ?? 2000}
            min={100}
            max={16000}
            step={100}
            onChange={(value) => updateRetrieval({ ...retrieval, context: { ...context, max_tokens: value ?? 2000 } })}
          />
        </div>
        <div>
          <FieldLabel label="Deduplication" help="Supprimer les morceaux trop similaires dans le contexte final." />
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
        {dedup.enabled ? (
          <div>
            <FieldLabel label="Dedup threshold" help="Seuil de similarite pour considerer un doublon." />
            <SliderInput
              value={dedup.similarity_threshold ?? 0.95}
              onChange={(value) =>
                updateRetrieval({
                  ...retrieval,
                  context: { ...context, deduplication: { ...dedup, similarity_threshold: value } },
                })
              }
              min={0}
              max={1}
              step={0.05}
            />
          </div>
        ) : null}
      </CollapsibleSection>
    </div>
  );
}
