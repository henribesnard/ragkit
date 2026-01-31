import { useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { CollapsibleSection } from '@/components/ui/collapsible-section';
import { FieldLabel } from '@/components/ui/field-label';
import { Input } from '@/components/ui/input';
import { MultiSelect } from '@/components/ui/multi-select';
import { NumberInput } from '@/components/ui/number-input';
import { Select } from '@/components/ui/select';
import { SliderInput } from '@/components/ui/slider-input';
import { ToggleSwitch } from '@/components/ui/toggle-switch';

interface WizardStepProps {
  config: Record<string, any>;
  onChange: (config: Record<string, any>) => void;
}

export function SourcesStep({ config, onChange }: WizardStepProps) {
  const ingestion = config.ingestion || {};
  const sources = ingestion.sources || [{}];
  const source = sources[0] || {};
  const chunking = ingestion.chunking || {};
  const fixed = chunking.fixed || {};
  const semantic = chunking.semantic || {};
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (fileInputRef.current) {
      fileInputRef.current.setAttribute('webkitdirectory', '');
      fileInputRef.current.setAttribute('directory', '');
    }
  }, []);

  const updateIngestion = (nextIngestion: any) => {
    onChange({ ...config, ingestion: nextIngestion });
  };

  const updateSource = (updates: any) => {
    const nextSource = { ...source, ...updates };
    updateIngestion({ ...ingestion, sources: [nextSource, ...sources.slice(1)] });
  };

  const handleBrowse = () => {
    fileInputRef.current?.click();
  };

  const handleBrowseChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) {
      return;
    }
    const relative = (files[0] as File & { webkitRelativePath?: string }).webkitRelativePath;
    if (relative) {
      const top = relative.split('/')[0];
      updateSource({ path: `./${top}` });
    }
  };

  const patternOptions = [
    { value: '*.pdf', label: '*.pdf' },
    { value: '*.md', label: '*.md' },
    { value: '*.txt', label: '*.txt' },
    { value: '*.docx', label: '*.docx' },
    { value: '*.html', label: '*.html' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <FieldLabel label="Source type" help="Type de source pour l'ingestion." />
        <Select
          value={source.type || 'local'}
          onChange={(event) => updateSource({ type: event.target.value })}
        >
          <option value="local">Local filesystem</option>
        </Select>
      </div>
      <div>
        <FieldLabel label="Path" help="Repertoire contenant vos documents." />
        <div className="flex gap-2">
          <Input
            placeholder="./data/documents"
            value={source.path || ''}
            onChange={(event) => updateSource({ path: event.target.value })}
            className="flex-1"
          />
          <Button type="button" variant="outline" onClick={handleBrowse}>
            Browse
          </Button>
          <input ref={fileInputRef} type="file" className="hidden" multiple onChange={handleBrowseChange} />
        </div>
      </div>
      <div>
        <FieldLabel label="Patterns" help="Formats de fichiers a indexer." />
        <MultiSelect
          options={patternOptions}
          selected={source.patterns || []}
          onChange={(selected) => updateSource({ patterns: selected })}
          allowCustom
        />
      </div>
      <div>
        <FieldLabel label="Recursive" help="Parcourt aussi les sous-dossiers." />
        <ToggleSwitch checked={source.recursive ?? true} onChange={(checked) => updateSource({ recursive: checked })} />
      </div>

      <CollapsibleSection title="Chunking">
        <div>
          <FieldLabel label="Strategy" help="fixed : taille fixe. semantic : coherence semantique." />
          <Select
            value={chunking.strategy || 'fixed'}
            onChange={(event) =>
              updateIngestion({ ...ingestion, chunking: { ...chunking, strategy: event.target.value } })
            }
          >
            <option value="fixed">Fixed</option>
            <option value="semantic">Semantic</option>
          </Select>
        </div>
        {chunking.strategy === 'semantic' ? (
          <>
            <div>
              <FieldLabel label="Similarity threshold" help="Seuil pour decouper en chunks." />
              <SliderInput
                value={semantic.similarity_threshold ?? 0.85}
                onChange={(value) =>
                  updateIngestion({
                    ...ingestion,
                    chunking: { ...chunking, semantic: { ...semantic, similarity_threshold: value } },
                  })
                }
                min={0}
                max={1}
                step={0.05}
              />
            </div>
            <div>
              <FieldLabel label="Min chunk size" help="Taille minimale d'un chunk." />
              <NumberInput
                value={semantic.min_chunk_size ?? 100}
                min={50}
                max={2000}
                step={50}
                onChange={(value) =>
                  updateIngestion({
                    ...ingestion,
                    chunking: { ...chunking, semantic: { ...semantic, min_chunk_size: value ?? 100 } },
                  })
                }
              />
            </div>
            <div>
              <FieldLabel label="Max chunk size" help="Taille maximale d'un chunk." />
              <NumberInput
                value={semantic.max_chunk_size ?? 1000}
                min={200}
                max={4000}
                step={100}
                onChange={(value) =>
                  updateIngestion({
                    ...ingestion,
                    chunking: { ...chunking, semantic: { ...semantic, max_chunk_size: value ?? 1000 } },
                  })
                }
              />
            </div>
          </>
        ) : (
          <>
            <div>
              <FieldLabel label="Chunk size" help="Nombre de caracteres par chunk." />
              <NumberInput
                value={fixed.chunk_size ?? 512}
                min={64}
                max={4096}
                step={64}
                onChange={(value) =>
                  updateIngestion({
                    ...ingestion,
                    chunking: { ...chunking, fixed: { ...fixed, chunk_size: value ?? 512 } },
                  })
                }
              />
            </div>
            <div>
              <FieldLabel label="Chunk overlap" help="Chevauchement entre chunks." />
              <NumberInput
                value={fixed.chunk_overlap ?? 50}
                min={0}
                max={512}
                step={10}
                onChange={(value) =>
                  updateIngestion({
                    ...ingestion,
                    chunking: { ...chunking, fixed: { ...fixed, chunk_overlap: value ?? 50 } },
                  })
                }
              />
            </div>
          </>
        )}
      </CollapsibleSection>
    </div>
  );
}
