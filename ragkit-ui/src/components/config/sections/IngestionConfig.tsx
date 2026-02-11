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

interface SectionProps {
  config: any;
  onChange: (value: any) => void;
}

export function IngestionConfigSection({ config, onChange }: SectionProps) {
  const { t } = useTranslation();
  const ingestion = config?.ingestion || {};
  const sources = ingestion.sources || [{}];
  const source = sources[0] || {};
  const parsing = ingestion.parsing || {};
  const ocr = parsing.ocr || {};
  const chunking = ingestion.chunking || {};
  const fixed = chunking.fixed || {};
  const semantic = chunking.semantic || {};
  const metadata = ingestion.metadata || {};
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
    const nextSources = [nextSource, ...sources.slice(1)];
    updateIngestion({ ...ingestion, sources: nextSources });
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
  const ocrLanguageOptions = [
    { value: 'eng', label: 'eng' },
    { value: 'fra', label: 'fra' },
    { value: 'deu', label: 'deu' },
    { value: 'spa', label: 'spa' },
    { value: 'ita', label: 'ita' },
  ];
  const metadataOptions = [
    { value: 'source_path', label: 'source_path' },
    { value: 'file_type', label: 'file_type' },
    { value: 'creation_date', label: 'creation_date' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <FieldLabel
          label={t('config.ingestion.sourcePathLabel')}
          help={t('config.ingestion.sourcePathHelp')}
        />
        <div className="flex gap-2">
          <Input
            value={source.path || ''}
            onChange={(event) => updateSource({ path: event.target.value })}
            className="flex-1"
          />
          <Button type="button" variant="outline" onClick={handleBrowse}>
            {t('common.actions.browse')}
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            multiple
            onChange={handleBrowseChange}
          />
        </div>
      </div>
      <div>
        <FieldLabel
          label={t('config.ingestion.patternsLabel')}
          help={t('config.ingestion.patternsHelp')}
        />
        <MultiSelect
          options={patternOptions}
          selected={source.patterns || []}
          onChange={(selected) => updateSource({ patterns: selected })}
          allowCustom
        />
      </div>
      <div>
        <FieldLabel
          label={t('config.ingestion.recursiveLabel')}
          help={t('config.ingestion.recursiveHelp')}
        />
        <ToggleSwitch checked={source.recursive ?? true} onChange={(checked) => updateSource({ recursive: checked })} />
      </div>

      <CollapsibleSection title={t('config.ingestion.parsingTitle')}>
        <div>
          <FieldLabel
            label={t('config.ingestion.parsingEngineLabel')}
            help={t('config.ingestion.parsingEngineHelp')}
          />
          <Select
            value={parsing.engine || 'auto'}
            onChange={(event) => updateIngestion({ ...ingestion, parsing: { ...parsing, engine: event.target.value } })}
          >
            <option value="auto">{t('common.options.auto')}</option>
            <option value="unstructured">Unstructured</option>
            <option value="docling">Docling</option>
            <option value="pypdf">PyPDF</option>
          </Select>
        </div>
        <div>
          <FieldLabel
            label={t('config.ingestion.ocrEnabledLabel')}
            help={t('config.ingestion.ocrEnabledHelp')}
          />
          <ToggleSwitch
            checked={ocr.enabled ?? false}
            onChange={(checked) =>
              updateIngestion({ ...ingestion, parsing: { ...parsing, ocr: { ...ocr, enabled: checked } } })
            }
          />
        </div>
        {ocr.enabled ? (
          <>
            <div>
              <FieldLabel
                label={t('config.ingestion.ocrEngineLabel')}
                help={t('config.ingestion.ocrEngineHelp')}
              />
              <Select
                value={ocr.engine || 'tesseract'}
                onChange={(event) =>
                  updateIngestion({ ...ingestion, parsing: { ...parsing, ocr: { ...ocr, engine: event.target.value } } })
                }
              >
                <option value="tesseract">Tesseract</option>
                <option value="easyocr">EasyOCR</option>
              </Select>
            </div>
            <div>
              <FieldLabel
                label={t('config.ingestion.ocrLanguagesLabel')}
                help={t('config.ingestion.ocrLanguagesHelp')}
              />
              <MultiSelect
                options={ocrLanguageOptions}
                selected={ocr.languages || []}
                onChange={(selected) =>
                  updateIngestion({ ...ingestion, parsing: { ...parsing, ocr: { ...ocr, languages: selected } } })
                }
                allowCustom
              />
            </div>
          </>
        ) : null}
      </CollapsibleSection>

      <CollapsibleSection title={t('config.ingestion.chunkingTitle')}>
        <div>
          <FieldLabel
            label={t('config.ingestion.strategyLabel')}
            help={t('config.ingestion.strategyHelp')}
          />
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
              <FieldLabel
                label={t('config.ingestion.similarityLabel')}
                help={t('config.ingestion.similarityHelp')}
              />
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
              <FieldLabel
                label={t('config.ingestion.minChunkLabel')}
                help={t('config.ingestion.minChunkHelp')}
              />
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
              <FieldLabel
                label={t('config.ingestion.maxChunkLabel')}
                help={t('config.ingestion.maxChunkHelp')}
              />
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
              <FieldLabel
                label={t('config.ingestion.chunkSizeLabel')}
                help={t('config.ingestion.chunkSizeHelp')}
              />
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
              <FieldLabel
                label={t('config.ingestion.chunkOverlapLabel')}
                help={t('config.ingestion.chunkOverlapHelp')}
              />
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

      <CollapsibleSection title={t('config.ingestion.metadataTitle')}>
        <div>
          <FieldLabel
            label={t('config.ingestion.metadataLabel')}
            help={t('config.ingestion.metadataHelp')}
          />
          <MultiSelect
            options={metadataOptions}
            selected={metadata.extract || []}
            onChange={(selected) => updateIngestion({ ...ingestion, metadata: { ...metadata, extract: selected } })}
            allowCustom
          />
        </div>
      </CollapsibleSection>
    </div>
  );
}
