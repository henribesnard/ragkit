import { FieldLabel } from '@/components/ui/field-label';
import { NumberInput } from '@/components/ui/number-input';
import { Select } from '@/components/ui/select';
import { SliderInput } from '@/components/ui/slider-input';
import { ToggleSwitch } from '@/components/ui/toggle-switch';

interface IntermediateSettingsProps {
  config: Record<string, any>;
  onChange: (config: Record<string, any>) => void;
}

const setNestedValue = (base: Record<string, any>, path: string[], value: any) => {
  let cursor = base;
  path.forEach((segment, index) => {
    if (index === path.length - 1) {
      cursor[segment] = value;
    } else {
      cursor[segment] = cursor[segment] ?? {};
      cursor = cursor[segment];
    }
  });
};

export function IntermediateSettings({ config, onChange }: IntermediateSettingsProps) {
  const ingestion = config?.ingestion ?? {};
  const chunking = ingestion.chunking ?? {};
  const fixed = chunking.fixed ?? {};
  const retrieval = config?.retrieval ?? {};
  const semantic = retrieval.semantic ?? {};
  const lexical = retrieval.lexical ?? {};
  const llmPrimary = config?.llm?.primary ?? {};
  const llmParams = llmPrimary.params ?? {};
  const behavior = config?.agents?.response_generator?.behavior ?? {};

  const alpha = semantic.weight ?? 0.5;
  const topK = semantic.top_k ?? lexical.top_k ?? 10;

  const updateConfig = (path: string[], value: any) => {
    const next = JSON.parse(JSON.stringify(config || {}));
    setNestedValue(next, path, value);
    onChange(next);
  };

  const updateAlpha = (nextAlpha: number) => {
    const next = JSON.parse(JSON.stringify(config || {}));
    setNestedValue(next, ['retrieval', 'semantic', 'weight'], nextAlpha);
    setNestedValue(next, ['retrieval', 'lexical', 'weight'], 1 - nextAlpha);
    setNestedValue(next, ['retrieval', 'semantic', 'enabled'], true);
    setNestedValue(next, ['retrieval', 'lexical', 'enabled'], true);
    setNestedValue(next, ['retrieval', 'architecture'], 'hybrid');
    onChange(next);
  };

  const updateTopK = (value: number | null) => {
    const nextValue = value ?? 10;
    const next = JSON.parse(JSON.stringify(config || {}));
    setNestedValue(next, ['retrieval', 'semantic', 'top_k'], nextValue);
    setNestedValue(next, ['retrieval', 'lexical', 'top_k'], nextValue);
    onChange(next);
  };

  return (
    <div className="space-y-6">
      <section className="space-y-4 rounded-3xl bg-white/70 p-6 shadow-soft">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-muted">Chunking</p>
          <h4 className="mt-2 text-lg font-display">Control context granularity</h4>
        </div>
        <div>
          <FieldLabel label="Strategy" help="Choisir entre decoupage fixe ou semantique." />
          <Select
            value={chunking.strategy || 'fixed'}
            onChange={(event) => updateConfig(['ingestion', 'chunking', 'strategy'], event.target.value)}
          >
            <option value="fixed">Fixed</option>
            <option value="semantic">Semantic</option>
          </Select>
        </div>
        <div>
          <FieldLabel label="Chunk size" help="Taille des morceaux (caracteres)." />
          <NumberInput
            value={fixed.chunk_size ?? 512}
            min={64}
            max={4096}
            step={64}
            onChange={(value) => updateConfig(['ingestion', 'chunking', 'fixed', 'chunk_size'], value ?? 512)}
          />
        </div>
        <div>
          <FieldLabel label="Chunk overlap" help="Chevauchement entre morceaux." />
          <NumberInput
            value={fixed.chunk_overlap ?? 50}
            min={0}
            max={512}
            step={10}
            onChange={(value) => updateConfig(['ingestion', 'chunking', 'fixed', 'chunk_overlap'], value ?? 50)}
          />
        </div>
      </section>

      <section className="space-y-4 rounded-3xl bg-white/70 p-6 shadow-soft">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-muted">Retrieval</p>
          <h4 className="mt-2 text-lg font-display">Blend semantic and lexical search</h4>
        </div>
        <div>
          <FieldLabel label="Architecture" help="Mode de recherche principal." />
          <Select
            value={retrieval.architecture || 'semantic'}
            onChange={(event) => updateConfig(['retrieval', 'architecture'], event.target.value)}
          >
            <option value="semantic">Semantic</option>
            <option value="lexical">Lexical</option>
            <option value="hybrid">Hybrid</option>
            <option value="hybrid_rerank">Hybrid + Rerank</option>
          </Select>
        </div>
        <div>
          <FieldLabel label="Top K" help="Nombre de resultats par requete." />
          <NumberInput value={topK} min={1} max={50} step={1} onChange={updateTopK} />
        </div>
        <div>
          <FieldLabel label="Semantic/Lexical balance" help="0 = lexical, 1 = semantic." />
          <SliderInput value={alpha} min={0} max={1} step={0.05} onChange={updateAlpha} />
        </div>
      </section>

      <section className="space-y-4 rounded-3xl bg-white/70 p-6 shadow-soft">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-muted">Generation</p>
          <h4 className="mt-2 text-lg font-display">Tone and output length</h4>
        </div>
        <div>
          <FieldLabel label="Temperature" help="Creativite du modele." />
          <SliderInput
            value={llmParams.temperature ?? 0.7}
            min={0}
            max={2}
            step={0.1}
            onChange={(value) => updateConfig(['llm', 'primary', 'params', 'temperature'], value)}
          />
        </div>
        <div>
          <FieldLabel label="Max tokens" help="Limite de tokens de reponse." />
          <NumberInput
            value={llmParams.max_tokens ?? null}
            min={100}
            max={8000}
            step={100}
            onChange={(value) => updateConfig(['llm', 'primary', 'params', 'max_tokens'], value)}
          />
        </div>
        <div>
          <FieldLabel label="Require citations" help="Forcer l'inclusion des sources." />
          <ToggleSwitch
            checked={behavior.cite_sources ?? true}
            onChange={(checked) =>
              updateConfig(['agents', 'response_generator', 'behavior', 'cite_sources'], checked)
            }
          />
        </div>
      </section>
    </div>
  );
}
