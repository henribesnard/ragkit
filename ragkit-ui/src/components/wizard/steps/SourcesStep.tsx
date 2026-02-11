import { useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
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
  const { t } = useTranslation();
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
    { value: '*.doc', label: '*.doc' },
    { value: '*.html', label: '*.html' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <FieldLabel label={t('wizard.sources.sourceTypeLabel')} help={t('wizard.sources.sourceTypeHelp')} />
        <Select
          value={source.type || 'local'}
          onChange={(event) => updateSource({ type: event.target.value })}
        >
          <option value="local">{t('wizard.sources.sourceTypeLocal')}</option>
        </Select>
      </div>
      <div>
        <FieldLabel label={t('wizard.sources.pathLabel')} help={t('wizard.sources.pathHelp')} />
        <div className="flex gap-2">
          <Input
            placeholder={t('wizard.sources.pathPlaceholder')}
            value={source.path || ''}
            onChange={(event) => updateSource({ path: event.target.value })}
            className="flex-1"
          />
          <Button type="button" variant="outline" onClick={handleBrowse}>
            {t('common.actions.browse')}
          </Button>
          <input ref={fileInputRef} type="file" className="hidden" multiple onChange={handleBrowseChange} />
        </div>
      </div>
      <div>
        <FieldLabel label={t('wizard.sources.patternsLabel')} help={t('wizard.sources.patternsHelp')} />
        <MultiSelect
          options={patternOptions}
          selected={source.patterns || []}
          onChange={(selected) => updateSource({ patterns: selected })}
          allowCustom
        />
      </div>
      <div>
        <FieldLabel label={t('wizard.sources.recursiveLabel')} help={t('wizard.sources.recursiveHelp')} />
        <ToggleSwitch checked={source.recursive ?? true} onChange={(checked) => updateSource({ recursive: checked })} />
      </div>

      <CollapsibleSection title={t('wizard.sources.chunkingTitle')}>
        <div>
          <FieldLabel label={t('wizard.sources.strategyLabel')} help={t('wizard.sources.strategyHelp')} />
          <Select
            value={chunking.strategy || 'fixed'}
            onChange={(event) =>
              updateIngestion({ ...ingestion, chunking: { ...chunking, strategy: event.target.value } })
            }
          >
            <option value="fixed">{t('common.chunking.fixed')}</option>
            <option value="semantic">{t('common.chunking.semantic')}</option>
          </Select>
        </div>
        {chunking.strategy === 'semantic' ? (
          <>
            <div>
              <FieldLabel label={t('wizard.sources.similarityLabel')} help={t('wizard.sources.similarityHelp')} />
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
              <FieldLabel label={t('wizard.sources.minChunkLabel')} help={t('wizard.sources.minChunkHelp')} />
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
              <FieldLabel label={t('wizard.sources.maxChunkLabel')} help={t('wizard.sources.maxChunkHelp')} />
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
              <FieldLabel label={t('wizard.sources.chunkSizeLabel')} help={t('wizard.sources.chunkSizeHelp')} />
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
              <FieldLabel label={t('wizard.sources.chunkOverlapLabel')} help={t('wizard.sources.chunkOverlapHelp')} />
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
