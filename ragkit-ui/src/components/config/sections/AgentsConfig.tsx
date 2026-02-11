import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { CollapsibleSection } from '@/components/ui/collapsible-section';
import { FieldLabel } from '@/components/ui/field-label';
import { Input } from '@/components/ui/input';
import { MultiSelect } from '@/components/ui/multi-select';
import { NumberInput } from '@/components/ui/number-input';
import { Select } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { ToggleSwitch } from '@/components/ui/toggle-switch';

interface SectionProps {
  config: any;
  onChange: (value: any) => void;
}

const intentOptions = [
  { value: 'question', labelKey: 'config.agents.intents.question' },
  { value: 'greeting', labelKey: 'config.agents.intents.greeting' },
  { value: 'chitchat', labelKey: 'config.agents.intents.chitchat' },
  { value: 'out_of_scope', labelKey: 'config.agents.intents.outOfScope' },
  { value: 'clarification', labelKey: 'config.agents.intents.clarification' },
];

const responseLangOptions = ['auto', 'match_query', 'match_documents', 'fr', 'en', 'es', 'de', 'it', 'pt'];

export function AgentsConfigSection({ config, onChange }: SectionProps) {
  const { t } = useTranslation();
  const agents = config?.agents || {};
  const queryAnalyzer = agents.query_analyzer || {};
  const qaBehavior = queryAnalyzer.behavior || {};
  const qaRewriting = qaBehavior.query_rewriting || {};
  const responseGenerator = agents.response_generator || {};
  const responseBehavior = responseGenerator.behavior || {};
  const globalConfig = agents.global || agents.global_config || {};
  const [schemaText, setSchemaText] = useState('');
  const schemaInitialized = useRef(false);

  useEffect(() => {
    if (schemaInitialized.current) {
      return;
    }
    if (queryAnalyzer.output_schema) {
      setSchemaText(JSON.stringify(queryAnalyzer.output_schema, null, 2));
      schemaInitialized.current = true;
    }
  }, [queryAnalyzer.output_schema]);

  const updateAgents = (nextAgents: any) => {
    onChange({ ...config, agents: nextAgents });
  };

  const updateQueryAnalyzer = (updates: any) => {
    updateAgents({ ...agents, query_analyzer: { ...queryAnalyzer, ...updates } });
  };

  const updateResponseGenerator = (updates: any) => {
    updateAgents({ ...agents, response_generator: { ...responseGenerator, ...updates } });
  };

  const isPresetLang = responseLangOptions.includes(responseBehavior.response_language || 'auto');
  const langSelectValue = isPresetLang ? responseBehavior.response_language || 'auto' : 'custom';

  const responseLangLabels: Record<string, string> = {
    auto: t('common.options.auto'),
    match_query: t('config.agents.matchQuery'),
    match_documents: t('config.agents.matchDocuments'),
    fr: t('common.languages.fr'),
    en: t('common.languages.en'),
    es: t('common.languages.es'),
    de: t('common.languages.de'),
    it: t('common.languages.it'),
    pt: t('common.languages.pt'),
  };

  return (
    <div className="space-y-8">
      <div>
        <FieldLabel
          label={t('config.agents.modeLabel')}
          help={t('config.agents.modeHelp')}
        />
        <Select
          value={agents.mode || 'default'}
          onChange={(event) => updateAgents({ ...agents, mode: event.target.value })}
        >
          <option value="default">{t('common.options.default')}</option>
          <option value="custom">{t('common.labels.custom')}</option>
        </Select>
      </div>

      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-ink">{t('config.agents.queryAnalyzerTitle')}</h3>
        <div>
          <FieldLabel label={t('config.agents.llmReferenceLabel')} help={t('config.agents.llmReferenceHelp')} />
          <Select
            value={queryAnalyzer.llm || 'fast'}
            onChange={(event) => updateQueryAnalyzer({ llm: event.target.value })}
          >
            <option value="primary">{t('config.agents.primary')}</option>
            <option value="secondary">{t('config.agents.secondary')}</option>
            <option value="fast">{t('config.agents.fast')}</option>
          </Select>
        </div>
        <div>
          <FieldLabel
            label={t('config.agents.systemPromptLabel')}
            help={t('config.agents.systemPromptHelp')}
          />
          <Textarea
            rows={6}
            value={queryAnalyzer.system_prompt || ''}
            onChange={(event) => updateQueryAnalyzer({ system_prompt: event.target.value })}
          />
        </div>
        <div>
          <FieldLabel
            label={t('config.agents.outputSchemaLabel')}
            help={t('config.agents.outputSchemaHelp')}
          />
          <Textarea
            rows={6}
            value={schemaText}
            onChange={(event) => {
              const next = event.target.value;
              setSchemaText(next);
              try {
                const parsed = JSON.parse(next);
                updateQueryAnalyzer({ output_schema: parsed });
              } catch {
                // keep text until valid JSON
              }
            }}
          />
        </div>

        <CollapsibleSection title={t('config.agents.behaviorTitle')}>
          <div>
            <FieldLabel
              label={t('config.agents.alwaysRetrieveLabel')}
              help={t('config.agents.alwaysRetrieveHelp')}
            />
            <ToggleSwitch
              checked={qaBehavior.always_retrieve ?? false}
              onChange={(checked) =>
                updateQueryAnalyzer({ behavior: { ...qaBehavior, always_retrieve: checked } })
              }
            />
          </div>
          <div>
            <FieldLabel
              label={t('config.agents.detectIntentsLabel')}
              help={t('config.agents.detectIntentsHelp')}
            />
            <MultiSelect
              options={intentOptions.map((option) => ({
                value: option.value,
                label: t(option.labelKey),
              }))}
              selected={qaBehavior.detect_intents || []}
              onChange={(selected) =>
                updateQueryAnalyzer({ behavior: { ...qaBehavior, detect_intents: selected } })
              }
              allowCustom
            />
          </div>
          <div>
            <FieldLabel label={t('config.agents.queryRewritingLabel')} help={t('config.agents.queryRewritingHelp')} />
            <ToggleSwitch
              checked={qaRewriting.enabled ?? true}
              onChange={(checked) =>
                updateQueryAnalyzer({
                  behavior: { ...qaBehavior, query_rewriting: { ...qaRewriting, enabled: checked } },
                })
              }
            />
          </div>
          {qaRewriting.enabled ? (
            <div>
              <FieldLabel label={t('config.agents.numRewritesLabel')} help={t('config.agents.numRewritesHelp')} />
              <NumberInput
                value={qaRewriting.num_rewrites ?? 1}
                min={1}
                max={3}
                step={1}
                onChange={(value) =>
                  updateQueryAnalyzer({
                    behavior: { ...qaBehavior, query_rewriting: { ...qaRewriting, num_rewrites: value ?? 1 } },
                  })
                }
              />
            </div>
          ) : null}
        </CollapsibleSection>
      </div>

      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-ink">{t('config.agents.responseGeneratorTitle')}</h3>
        <div>
          <FieldLabel label={t('config.agents.llmReferenceLabel')} help={t('config.agents.responseLlmHelp')} />
          <Select
            value={responseGenerator.llm || 'primary'}
            onChange={(event) => updateResponseGenerator({ llm: event.target.value })}
          >
            <option value="primary">{t('config.agents.primary')}</option>
            <option value="secondary">{t('config.agents.secondary')}</option>
            <option value="fast">{t('config.agents.fast')}</option>
          </Select>
        </div>
        <div>
          <FieldLabel
            label={t('config.agents.systemPromptLabel')}
            help={t('config.agents.responsePromptHelp')}
          />
          <Textarea
            rows={8}
            value={responseGenerator.system_prompt || ''}
            onChange={(event) => updateResponseGenerator({ system_prompt: event.target.value })}
          />
        </div>
        <div>
          <FieldLabel label={t('config.agents.noRetrievalLabel')} help={t('config.agents.noRetrievalHelp')} />
          <Textarea
            rows={4}
            value={responseGenerator.no_retrieval_prompt || ''}
            onChange={(event) => updateResponseGenerator({ no_retrieval_prompt: event.target.value })}
          />
        </div>
        <div>
          <FieldLabel label={t('config.agents.outOfScopeLabel')} help={t('config.agents.outOfScopeHelp')} />
          <Textarea
            rows={4}
            value={responseGenerator.out_of_scope_prompt || ''}
            onChange={(event) => updateResponseGenerator({ out_of_scope_prompt: event.target.value })}
          />
        </div>

        <CollapsibleSection title={t('config.agents.behaviorTitle')}>
          <div>
            <FieldLabel label={t('config.agents.citeSourcesLabel')} help={t('config.agents.citeSourcesHelp')} />
            <ToggleSwitch
              checked={responseBehavior.cite_sources ?? true}
              onChange={(checked) =>
                updateResponseGenerator({ behavior: { ...responseBehavior, cite_sources: checked } })
              }
            />
          </div>
          <div>
            <FieldLabel
              label={t('config.agents.sourcePathLabel')}
              help={t('config.agents.sourcePathHelp')}
            />
            <Select
              value={responseBehavior.source_path_mode || 'basename'}
              onChange={(event) =>
                updateResponseGenerator({ behavior: { ...responseBehavior, source_path_mode: event.target.value } })
              }
            >
              <option value="basename">{t('config.agents.basename')}</option>
              <option value="full">{t('config.agents.fullPath')}</option>
            </Select>
          </div>
          <div>
            <FieldLabel label={t('config.agents.citationFormatLabel')} help={t('config.agents.citationFormatHelp')} />
            <Input
              value={responseBehavior.citation_format || ''}
              onChange={(event) =>
                updateResponseGenerator({ behavior: { ...responseBehavior, citation_format: event.target.value } })
              }
            />
          </div>
          <div>
            <FieldLabel label={t('config.agents.admitLabel')} help={t('config.agents.admitHelp')} />
            <ToggleSwitch
              checked={responseBehavior.admit_uncertainty ?? true}
              onChange={(checked) =>
                updateResponseGenerator({ behavior: { ...responseBehavior, admit_uncertainty: checked } })
              }
            />
          </div>
          <div>
            <FieldLabel label={t('config.agents.uncertaintyLabel')} help={t('config.agents.uncertaintyHelp')} />
            <Input
              value={responseBehavior.uncertainty_phrase || ''}
              onChange={(event) =>
                updateResponseGenerator({ behavior: { ...responseBehavior, uncertainty_phrase: event.target.value } })
              }
            />
          </div>
          <div>
            <FieldLabel label={t('config.agents.maxResponseLabel')} help={t('config.agents.maxResponseHelp')} />
            <NumberInput
              value={responseBehavior.max_response_length ?? null}
              min={1}
              max={10000}
              step={1}
              onChange={(value) =>
                updateResponseGenerator({ behavior: { ...responseBehavior, max_response_length: value } })
              }
            />
          </div>
          <div>
            <FieldLabel label={t('config.agents.responseLanguageLabel')} help={t('config.agents.responseLanguageHelp')} />
            <Select
              value={langSelectValue}
              onChange={(event) => {
                const next = event.target.value;
                if (next !== 'custom') {
                  updateResponseGenerator({ behavior: { ...responseBehavior, response_language: next } });
                }
              }}
            >
              {responseLangOptions.map((option) => (
                <option key={option} value={option}>
                  {responseLangLabels[option] || option}
                </option>
              ))}
              <option value="custom">{t('common.labels.custom')}</option>
            </Select>
            {langSelectValue === 'custom' ? (
              <Input
                className="mt-2"
                value={responseBehavior.response_language || ''}
                onChange={(event) =>
                  updateResponseGenerator({ behavior: { ...responseBehavior, response_language: event.target.value } })
                }
                placeholder="ex: fr-CA"
              />
            ) : null}
          </div>
        </CollapsibleSection>
      </div>

      <CollapsibleSection title={t('config.agents.globalTitle')}>
        <div>
          <FieldLabel label={t('wizard.llm.timeoutLabel')} help={t('config.agents.globalTimeoutHelp')} />
          <NumberInput
            value={globalConfig.timeout ?? 30}
            min={1}
            max={120}
            step={1}
            unit="s"
            onChange={(value) => updateAgents({ ...agents, global: { ...globalConfig, timeout: value ?? 30 } })}
          />
        </div>
        <div>
          <FieldLabel label={t('wizard.llm.maxRetriesLabel')} help={t('config.agents.globalRetriesHelp')} />
          <NumberInput
            value={globalConfig.max_retries ?? 2}
            min={0}
            max={5}
            step={1}
            onChange={(value) => updateAgents({ ...agents, global: { ...globalConfig, max_retries: value ?? 2 } })}
          />
        </div>
        <div>
          <FieldLabel label={t('config.agents.retryDelayLabel')} help={t('config.agents.retryDelayHelp')} />
          <NumberInput
            value={globalConfig.retry_delay ?? 1}
            min={0}
            max={10}
            step={1}
            unit="s"
            onChange={(value) => updateAgents({ ...agents, global: { ...globalConfig, retry_delay: value ?? 1 } })}
          />
        </div>
        <div>
          <FieldLabel label={t('config.agents.verboseLabel')} help={t('config.agents.verboseHelp')} />
          <ToggleSwitch
            checked={globalConfig.verbose ?? false}
            onChange={(checked) => updateAgents({ ...agents, global: { ...globalConfig, verbose: checked } })}
          />
        </div>
      </CollapsibleSection>
    </div>
  );
}
