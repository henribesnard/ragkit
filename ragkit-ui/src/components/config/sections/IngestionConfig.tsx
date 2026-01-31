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

interface SectionProps {
  config: any;
  onChange: (value: any) => void;
}

export function IngestionConfigSection({ config, onChange }: SectionProps) {
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
          label="Source path"
          help="Repertoire contenant les documents qui constitueront votre base de connaissances. Chemin relatif depuis la racine du projet."
        />
        <div className="flex gap-2">
          <Input
            value={source.path || ''}
            onChange={(event) => updateSource({ path: event.target.value })}
            className="flex-1"
          />
          <Button type="button" variant="outline" onClick={handleBrowse}>
            Browse
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
          label="Patterns"
          help="Types de fichiers a indexer. Selectionnez les formats de vos documents."
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
          label="Recursive"
          help="Si active, parcourt aussi les sous-dossiers du repertoire source."
        />
        <ToggleSwitch checked={source.recursive ?? true} onChange={(checked) => updateSource({ recursive: checked })} />
      </div>

      <CollapsibleSection title="Parsing">
        <div>
          <FieldLabel
            label="Parsing engine"
            help="Moteur d'extraction de texte. auto detecte automatiquement le meilleur moteur selon le type de fichier. unstructured et docling supportent plus de formats. pypdf est leger et rapide pour les PDF simples."
          />
          <Select
            value={parsing.engine || 'auto'}
            onChange={(event) => updateIngestion({ ...ingestion, parsing: { ...parsing, engine: event.target.value } })}
          >
            <option value="auto">Auto</option>
            <option value="unstructured">Unstructured</option>
            <option value="docling">Docling</option>
            <option value="pypdf">PyPDF</option>
          </Select>
        </div>
        <div>
          <FieldLabel
            label="OCR enabled"
            help="Active la reconnaissance optique de caracteres pour les PDF scannes et les images. Necessite un moteur OCR installe."
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
                label="OCR engine"
                help="tesseract : moteur OCR open-source classique, rapide. easyocr : base sur le deep learning, meilleur sur les langues non-latines."
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
                label="OCR languages"
                help="Langues des documents pour l'OCR. Ajouter les codes de langue pertinents."
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

      <CollapsibleSection title="Chunking">
        <div>
          <FieldLabel
            label="Strategy"
            help="fixed : decoupe en morceaux de taille fixe (simple et rapide). semantic : decoupe en suivant la coherence semantique du texte."
          />
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
              <FieldLabel
                label="Similarity threshold"
                help="Seuil de similarite pour determiner ou couper. Plus haut = morceaux plus granulaires. Plus bas = morceaux plus larges."
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
                label="Min chunk size"
                help="Taille minimale d'un chunk semantique. Les morceaux trop petits sont fusionnes."
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
                label="Max chunk size"
                help="Taille maximale d'un chunk semantique. Au-dela, le texte est coupe."
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
                label="Chunk size"
                help="Nombre de caracteres par morceau. Plus petit = plus precis. Plus grand = plus de contexte par resultat."
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
                label="Chunk overlap"
                help="Nombre de caracteres de chevauchement entre les morceaux consecutifs. Evite de couper une phrase."
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

      <CollapsibleSection title="Metadata">
        <div>
          <FieldLabel
            label="Extract fields"
            help="Metadonnees extraites automatiquement de chaque document et stockees avec les chunks. Utiles pour le filtrage a la recherche."
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
