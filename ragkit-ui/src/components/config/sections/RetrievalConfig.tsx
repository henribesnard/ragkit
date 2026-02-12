import { useTranslation } from 'react-i18next';
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
  const { t } = useTranslation();
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
          label={t('wizard.retrieval.architectureLabel')}
          help={t('config.retrieval.architectureHelp')}
        />
        <Select
          value={retrieval.architecture || 'semantic'}
          onChange={(event) => updateRetrieval({ ...retrieval, architecture: event.target.value })}
        >
          <option value="semantic">{t('common.retrieval.semantic')}</option>
          <option value="lexical">{t('common.retrieval.lexical')}</option>
          <option value="hybrid">{t('common.retrieval.hybrid')}</option>
          <option value="hybrid_rerank">{t('common.retrieval.hybridRerank')}</option>
        </Select>
      </div>

      {isSemantic ? (
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-ink">{t('config.retrieval.semanticTitle')}</h3>
          <div>
            <FieldLabel label={t('wizard.retrieval.enabledLabel')} help={t('config.retrieval.semanticEnabledHelp')} />
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
                label={t('wizard.retrieval.weightLabel')}
                help={t('config.retrieval.semanticWeightHelp')}
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
            <FieldLabel label={t('wizard.retrieval.topKLabel')} help={t('config.retrieval.semanticTopKHelp')} />
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
              label={t('wizard.retrieval.similarityLabel')}
              help={t('config.retrieval.semanticSimilarityHelp')}
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
          <h3 className="text-sm font-semibold text-ink">{t('config.retrieval.lexicalTitle')}</h3>
          <div>
            <FieldLabel label={t('wizard.retrieval.enabledLabel')} help={t('config.retrieval.lexicalEnabledHelp')} />
            <ToggleSwitch
              checked={lexical.enabled ?? false}
              onChange={(checked) =>
                updateRetrieval({ ...retrieval, lexical: { ...lexical, enabled: checked } })
              }
            />
          </div>
          {isHybrid ? (
            <div>
              <FieldLabel label={t('wizard.retrieval.weightLabel')} help={t('config.retrieval.lexicalWeightHelp')} />
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
            <FieldLabel label={t('wizard.retrieval.topKLabel')} help={t('config.retrieval.lexicalTopKHelp')} />
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
            <FieldLabel label={t('wizard.retrieval.algorithmLabel')} help={t('config.retrieval.algorithmHelp')} />
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

          <CollapsibleSection title={t('config.retrieval.bm25Title')}>
            <div>
              <FieldLabel label={t('wizard.retrieval.k1Label')} help={t('config.retrieval.k1Help')} />
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
              <FieldLabel label={t('wizard.retrieval.bLabel')} help={t('config.retrieval.bHelp')} />
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

          <CollapsibleSection title={t('config.retrieval.preprocessingTitle')}>
            <div>
              <FieldLabel label={t('config.retrieval.lowercaseLabel')} help={t('config.retrieval.lowercaseHelp')} />
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
              <FieldLabel label={t('config.retrieval.stopwordsLabel')} help={t('config.retrieval.stopwordsHelp')} />
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
              <FieldLabel label={t('config.retrieval.stopwordsLangLabel')} help={t('config.retrieval.stopwordsLangHelp')} />
              <Select
                value={lexicalPre.stopwords_lang || 'auto'}
                onChange={(event) =>
                  updateRetrieval({
                    ...retrieval,
                    lexical: { ...lexical, preprocessing: { ...lexicalPre, stopwords_lang: event.target.value } },
                  })
                }
              >
                <option value="auto">{t('common.options.auto')}</option>
                <option value="french">{t('common.languages.fr')}</option>
                <option value="english">{t('common.languages.en')}</option>
              </Select>
            </div>
            <div>
              <FieldLabel label={t('config.retrieval.stemmingLabel')} help={t('config.retrieval.stemmingHelp')} />
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
          <h3 className="text-sm font-semibold text-ink">{t('config.retrieval.rerankTitle')}</h3>
          <div>
            <FieldLabel label={t('wizard.retrieval.enabledLabel')} help={t('config.retrieval.rerankEnabledHelp')} />
            <ToggleSwitch
              checked={rerank.enabled ?? false}
              onChange={(checked) => updateRetrieval({ ...retrieval, rerank: { ...rerank, enabled: checked } })}
            />
          </div>
          <div>
            <FieldLabel label={t('wizard.embedding.providerLabel')} help={t('config.retrieval.rerankProviderHelp')} />
            <Select
              value={rerank.provider || 'none'}
              onChange={(event) => updateRetrieval({ ...retrieval, rerank: { ...rerank, provider: event.target.value } })}
            >
              <option value="none">{t('common.options.none')}</option>
              <option value="cohere">Cohere</option>
            </Select>
          </div>
          <div>
            <FieldLabel label={t('wizard.embedding.modelLabel')} help={t('config.retrieval.rerankModelHelp')} />
            <Input
              value={rerank.model || ''}
              onChange={(event) => updateRetrieval({ ...retrieval, rerank: { ...rerank, model: event.target.value } })}
            />
          </div>
          <div>
            <FieldLabel label={t('wizard.embedding.apiKeyLabel')} help={t('config.retrieval.rerankApiKeyHelp')} />
            <Input
              type="password"
              placeholder="sk-..."
              value={rerank.api_key || ''}
              onChange={(event) => updateRetrieval({ ...retrieval, rerank: { ...rerank, api_key: event.target.value } })}
            />
          </div>
          <div>
            <FieldLabel label={t('wizard.retrieval.topNLabel')} help={t('config.retrieval.rerankTopNHelp')} />
            <NumberInput
              value={rerank.top_n ?? 5}
              min={1}
              max={50}
              step={1}
              onChange={(value) => updateRetrieval({ ...retrieval, rerank: { ...rerank, top_n: value ?? 5 } })}
            />
          </div>
          <div>
            <FieldLabel label={t('config.retrieval.candidatesLabel')} help={t('config.retrieval.candidatesHelp')} />
            <NumberInput
              value={rerank.candidates ?? 40}
              min={1}
              max={200}
              step={1}
              onChange={(value) => updateRetrieval({ ...retrieval, rerank: { ...rerank, candidates: value ?? 40 } })}
            />
          </div>
          <div>
            <FieldLabel label={t('config.retrieval.rerankThresholdLabel')} help={t('config.retrieval.rerankThresholdHelp')} />
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
        <CollapsibleSection title={t('config.retrieval.fusionTitle')}>
          <div>
            <FieldLabel label={t('config.retrieval.fusionMethodLabel')} help={t('config.retrieval.fusionMethodHelp')} />
            <Select
              value={fusion.method || 'weighted_sum'}
              onChange={(event) => updateRetrieval({ ...retrieval, fusion: { ...fusion, method: event.target.value } })}
            >
              <option value="weighted_sum">{t('config.retrieval.fusionWeighted')}</option>
              <option value="reciprocal_rank_fusion">{t('config.retrieval.fusionRRF')}</option>
            </Select>
          </div>
          <div>
            <FieldLabel label={t('config.retrieval.normalizeLabel')} help={t('config.retrieval.normalizeHelp')} />
            <ToggleSwitch
              checked={fusion.normalize_scores ?? true}
              onChange={(checked) => updateRetrieval({ ...retrieval, fusion: { ...fusion, normalize_scores: checked } })}
            />
          </div>
          {fusion.method === 'reciprocal_rank_fusion' ? (
            <div>
              <FieldLabel label={t('config.retrieval.rrfLabel')} help={t('config.retrieval.rrfHelp')} />
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

      <CollapsibleSection title={t('wizard.retrieval.contextTitle')}>
        <div>
          <FieldLabel label={t('wizard.retrieval.maxChunksLabel')} help={t('config.retrieval.contextChunksHelp')} />
          <NumberInput
            value={context.max_chunks ?? 10}
            min={1}
            max={20}
            step={1}
            onChange={(value) => updateRetrieval({ ...retrieval, context: { ...context, max_chunks: value ?? 10 } })}
          />
        </div>
        <div>
          <FieldLabel label={t('wizard.retrieval.maxTokensLabel')} help={t('config.retrieval.contextTokensHelp')} />
          <NumberInput
            value={context.max_tokens ?? 2000}
            min={100}
            max={16000}
            step={100}
            onChange={(value) => updateRetrieval({ ...retrieval, context: { ...context, max_tokens: value ?? 2000 } })}
          />
        </div>
        <div>
          <FieldLabel label={t('wizard.retrieval.dedupLabel')} help={t('config.retrieval.dedupHelp')} />
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
            <FieldLabel label={t('config.retrieval.dedupThresholdLabel')} help={t('config.retrieval.dedupThresholdHelp')} />
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
