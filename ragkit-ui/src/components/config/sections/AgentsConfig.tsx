import { useEffect, useRef, useState } from 'react';
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
  { value: 'question', label: 'question' },
  { value: 'greeting', label: 'greeting' },
  { value: 'chitchat', label: 'chitchat' },
  { value: 'out_of_scope', label: 'out_of_scope' },
  { value: 'clarification', label: 'clarification' },
];

const responseLangOptions = ['auto', 'match_query', 'match_documents', 'fr', 'en', 'es', 'de', 'it', 'pt'];

export function AgentsConfigSection({ config, onChange }: SectionProps) {
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

  return (
    <div className="space-y-8">
      <div>
        <FieldLabel
          label="Mode"
          help="default : utilise le pipeline standard query -> retrieval -> response. custom : permet d'ajouter des agents personnalises."
        />
        <Select
          value={agents.mode || 'default'}
          onChange={(event) => updateAgents({ ...agents, mode: event.target.value })}
        >
          <option value="default">Default</option>
          <option value="custom">Custom</option>
        </Select>
      </div>

      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-ink">Query Analyzer</h3>
        <div>
          <FieldLabel label="LLM reference" help="Quel modele LLM utiliser pour analyser les requetes." />
          <Select
            value={queryAnalyzer.llm || 'fast'}
            onChange={(event) => updateQueryAnalyzer({ llm: event.target.value })}
          >
            <option value="primary">Primary</option>
            <option value="secondary">Secondary</option>
            <option value="fast">Fast</option>
          </Select>
        </div>
        <div>
          <FieldLabel
            label="System prompt"
            help="Instructions donnees au LLM pour analyser les requetes. Le LLM doit retourner un JSON." 
          />
          <Textarea
            rows={6}
            value={queryAnalyzer.system_prompt || ''}
            onChange={(event) => updateQueryAnalyzer({ system_prompt: event.target.value })}
          />
        </div>
        <div>
          <FieldLabel
            label="Output schema"
            help="Schema JSON que l'agent doit respecter pour la sortie."
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

        <CollapsibleSection title="Behavior">
          <div>
            <FieldLabel
              label="Always retrieve"
              help="Effectue toujours une recherche, meme pour salutations et hors-sujet."
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
              label="Detect intents"
              help="Types d'intentions que l'agent doit detecter."
            />
            <MultiSelect
              options={intentOptions}
              selected={qaBehavior.detect_intents || []}
              onChange={(selected) =>
                updateQueryAnalyzer({ behavior: { ...qaBehavior, detect_intents: selected } })
              }
              allowCustom
            />
          </div>
          <div>
            <FieldLabel label="Query rewriting" help="Reecrire la requete pour ameliorer la recherche." />
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
              <FieldLabel label="Num rewrites" help="Nombre de reformulations de la requete." />
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
        <h3 className="text-sm font-semibold text-ink">Response Generator</h3>
        <div>
          <FieldLabel label="LLM reference" help="Quel modele LLM utiliser pour generer les reponses." />
          <Select
            value={responseGenerator.llm || 'primary'}
            onChange={(event) => updateResponseGenerator({ llm: event.target.value })}
          >
            <option value="primary">Primary</option>
            <option value="secondary">Secondary</option>
            <option value="fast">Fast</option>
          </Select>
        </div>
        <div>
          <FieldLabel
            label="System prompt"
            help="Instructions pour generer les reponses. Utiliser {context} comme placeholder."
          />
          <Textarea
            rows={8}
            value={responseGenerator.system_prompt || ''}
            onChange={(event) => updateResponseGenerator({ system_prompt: event.target.value })}
          />
        </div>
        <div>
          <FieldLabel label="No retrieval prompt" help="Prompt utilise quand aucune recherche n'est necessaire." />
          <Textarea
            rows={4}
            value={responseGenerator.no_retrieval_prompt || ''}
            onChange={(event) => updateResponseGenerator({ no_retrieval_prompt: event.target.value })}
          />
        </div>
        <div>
          <FieldLabel label="Out of scope prompt" help="Prompt utilise quand la question est hors du domaine." />
          <Textarea
            rows={4}
            value={responseGenerator.out_of_scope_prompt || ''}
            onChange={(event) => updateResponseGenerator({ out_of_scope_prompt: event.target.value })}
          />
        </div>

        <CollapsibleSection title="Behavior">
          <div>
            <FieldLabel label="Cite sources" help="Inclure les references des sources dans la reponse." />
            <ToggleSwitch
              checked={responseBehavior.cite_sources ?? true}
              onChange={(checked) =>
                updateResponseGenerator({ behavior: { ...responseBehavior, cite_sources: checked } })
              }
            />
          </div>
          <div>
            <FieldLabel
              label="Source path mode"
              help="Controle la sortie des chemins sources (basename masque les chemins complets)."
            />
            <Select
              value={responseBehavior.source_path_mode || 'basename'}
              onChange={(event) =>
                updateResponseGenerator({ behavior: { ...responseBehavior, source_path_mode: event.target.value } })
              }
            >
              <option value="basename">Basename</option>
              <option value="full">Full path</option>
            </Select>
          </div>
          <div>
            <FieldLabel label="Citation format" help="Format des citations dans la reponse." />
            <Input
              value={responseBehavior.citation_format || ''}
              onChange={(event) =>
                updateResponseGenerator({ behavior: { ...responseBehavior, citation_format: event.target.value } })
              }
            />
          </div>
          <div>
            <FieldLabel
              label="Admit uncertainty"
              help="Si le LLM ne trouve pas de reponse, il l'admet au lieu d'inventer."
            />
            <ToggleSwitch
              checked={responseBehavior.admit_uncertainty ?? true}
              onChange={(checked) =>
                updateResponseGenerator({ behavior: { ...responseBehavior, admit_uncertainty: checked } })
              }
            />
          </div>
          <div>
            <FieldLabel label="Uncertainty phrase" help="Phrase utilisee quand le LLM ne peut pas repondre." />
            <Input
              value={responseBehavior.uncertainty_phrase || ''}
              onChange={(event) =>
                updateResponseGenerator({ behavior: { ...responseBehavior, uncertainty_phrase: event.target.value } })
              }
            />
          </div>
          <div>
            <FieldLabel label="Max response length" help="Limite la longueur de la reponse en caracteres." />
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
            <FieldLabel label="Response language" help="Langue de la reponse." />
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
                  {option}
                </option>
              ))}
              <option value="custom">Custom</option>
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

      <CollapsibleSection title="Global settings">
        <div>
          <FieldLabel label="Timeout" help="Temps maximum pour le traitement complet d'une requete." />
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
          <FieldLabel label="Max retries" help="Nombre de tentatives en cas d'echec d'un agent." />
          <NumberInput
            value={globalConfig.max_retries ?? 2}
            min={0}
            max={5}
            step={1}
            onChange={(value) => updateAgents({ ...agents, global: { ...globalConfig, max_retries: value ?? 2 } })}
          />
        </div>
        <div>
          <FieldLabel label="Retry delay" help="Delai entre les tentatives (secondes)." />
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
          <FieldLabel label="Verbose" help="Active les logs detailles des agents." />
          <ToggleSwitch
            checked={globalConfig.verbose ?? false}
            onChange={(checked) => updateAgents({ ...agents, global: { ...globalConfig, verbose: checked } })}
          />
        </div>
      </CollapsibleSection>
    </div>
  );
}
