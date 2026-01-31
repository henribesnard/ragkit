import { useEffect, useRef, useState } from 'react';
import { CollapsibleSection } from '@/components/ui/collapsible-section';
import { FieldLabel } from '@/components/ui/field-label';
import { Input } from '@/components/ui/input';
import { ModelSelect } from '@/components/ui/model-select';
import { NumberInput } from '@/components/ui/number-input';
import { Select } from '@/components/ui/select';
import { ToggleSwitch } from '@/components/ui/toggle-switch';
import { EMBEDDING_MODELS } from '@/data/models';

interface WizardStepProps {
  config: Record<string, any>;
  onChange: (config: Record<string, any>) => void;
}

const isSameModel = (left: any, right: any) => {
  if (!left || !right) {
    return false;
  }
  return left.provider === right.provider && left.model === right.model;
};

export function EmbeddingStep({ config, onChange }: WizardStepProps) {
  const embedding = config.embedding || {};
  const documentModel = embedding.document_model || {};
  const queryModel = embedding.query_model || {};
  const [sameAsDocument, setSameAsDocument] = useState(true);
  const initializedRef = useRef(false);

  useEffect(() => {
    if (initializedRef.current) {
      return;
    }
    if (documentModel.provider || queryModel.provider) {
      setSameAsDocument(isSameModel(documentModel, queryModel));
      initializedRef.current = true;
    }
  }, [documentModel, queryModel]);

  const updateEmbedding = (nextEmbedding: any) => {
    onChange({ ...config, embedding: nextEmbedding });
  };

  const updateDocumentModel = (updates: any) => {
    const nextDocument = { ...documentModel, ...updates };
    updateEmbedding({
      ...embedding,
      document_model: nextDocument,
      query_model: sameAsDocument ? { ...queryModel, ...nextDocument } : queryModel,
    });
  };

  const updateQueryModel = (updates: any) => {
    updateEmbedding({
      ...embedding,
      document_model: documentModel,
      query_model: { ...queryModel, ...updates },
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <FieldLabel label="Provider" help="Provider d'embedding." />
        <Select
          value={documentModel.provider || 'openai'}
          onChange={(event) => updateDocumentModel({ provider: event.target.value })}
        >
          <option value="openai">OpenAI</option>
          <option value="ollama">Ollama</option>
          <option value="cohere">Cohere</option>
          <option value="litellm">LiteLLM</option>
        </Select>
      </div>
      <div>
        <FieldLabel label="Model" help="Modele d'embedding." />
        <ModelSelect
          provider={documentModel.provider || 'openai'}
          models={EMBEDDING_MODELS}
          value={documentModel.model || ''}
          onChange={(value) => updateDocumentModel({ model: value })}
        />
      </div>
      {documentModel.provider !== 'ollama' ? (
        <div>
          <FieldLabel label="API key" help="Cle d'API pour le provider." />
          <Input
            type="password"
            placeholder="sk-..."
            value={documentModel.api_key || ''}
            onChange={(event) => updateDocumentModel({ api_key: event.target.value })}
          />
        </div>
      ) : null}

      <CollapsibleSection title="Parameters">
        <div>
          <FieldLabel label="Batch size" help="Nombre de textes par requete." />
          <NumberInput
            value={documentModel.params?.batch_size ?? null}
            min={1}
            max={2048}
            step={1}
            onChange={(value) => updateDocumentModel({ params: { ...documentModel.params, batch_size: value } })}
          />
        </div>
        <div>
          <FieldLabel label="Dimensions" help="Laisser vide pour la dimension par defaut." />
          <NumberInput
            value={documentModel.params?.dimensions ?? null}
            min={1}
            max={4096}
            step={1}
            onChange={(value) => updateDocumentModel({ params: { ...documentModel.params, dimensions: value } })}
          />
        </div>
        <div>
          <FieldLabel label="Cache enabled" help="Active le cache d'embeddings." />
          <ToggleSwitch
            checked={documentModel.cache?.enabled ?? false}
            onChange={(checked) => updateDocumentModel({ cache: { ...documentModel.cache, enabled: checked } })}
          />
        </div>
        {documentModel.cache?.enabled ? (
          <div>
            <FieldLabel label="Cache backend" help="memory ou disk." />
            <Select
              value={documentModel.cache?.backend || 'memory'}
              onChange={(event) => updateDocumentModel({ cache: { ...documentModel.cache, backend: event.target.value } })}
            >
              <option value="memory">Memory</option>
              <option value="disk">Disk</option>
            </Select>
          </div>
        ) : null}
      </CollapsibleSection>

      <div>
        <FieldLabel label="Same as document model" help="Utiliser le meme modele pour les requetes." />
        <ToggleSwitch
          checked={sameAsDocument}
          onChange={(checked) => {
            setSameAsDocument(checked);
            if (checked) {
              updateEmbedding({
                ...embedding,
                document_model: documentModel,
                query_model: { ...documentModel },
              });
            }
          }}
        />
      </div>

      {!sameAsDocument ? (
        <div className="space-y-4">
          <div>
            <FieldLabel label="Query provider" help="Provider pour le modele de requete." />
            <Select
              value={queryModel.provider || 'openai'}
              onChange={(event) => updateQueryModel({ provider: event.target.value })}
            >
              <option value="openai">OpenAI</option>
              <option value="ollama">Ollama</option>
              <option value="cohere">Cohere</option>
              <option value="litellm">LiteLLM</option>
            </Select>
          </div>
          <div>
            <FieldLabel label="Query model" help="Modele d'embedding pour les requetes." />
            <ModelSelect
              provider={queryModel.provider || 'openai'}
              models={EMBEDDING_MODELS}
              value={queryModel.model || ''}
              onChange={(value) => updateQueryModel({ model: value })}
            />
          </div>
          {queryModel.provider !== 'ollama' ? (
            <div>
              <FieldLabel label="Query API key" help="Cle d'API pour les requetes." />
              <Input
                type="password"
                placeholder="sk-..."
                value={queryModel.api_key || ''}
                onChange={(event) => updateQueryModel({ api_key: event.target.value })}
              />
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
