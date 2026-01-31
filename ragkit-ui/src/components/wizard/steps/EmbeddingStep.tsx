import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';

interface WizardStepProps {
  config: Record<string, any>;
  onChange: (config: Record<string, any>) => void;
}

export function EmbeddingStep({ config, onChange }: WizardStepProps) {
  const embedding = config.embedding || {};
  const documentModel = embedding.document_model || {};
  const provider = documentModel.provider || 'openai';
  const modelPlaceholder: Record<string, string> = {
    openai: 'text-embedding-3-large',
    ollama: 'nomic-embed-text',
    cohere: 'embed-multilingual-v3.0',
    litellm: 'mistral/mistral-embed',
  };

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold">Provider</p>
        <Select
          value={provider}
          onChange={(event) =>
            onChange({
              ...config,
              embedding: {
                ...embedding,
                document_model: { ...documentModel, provider: event.target.value },
                query_model: { ...documentModel, provider: event.target.value },
              },
            })
          }
        >
          <option value="openai">OpenAI</option>
          <option value="ollama">Ollama</option>
          <option value="cohere">Cohere</option>
          <option value="litellm">LiteLLM (generic)</option>
        </Select>
      </div>
      <div>
        <p className="text-sm font-semibold">Model</p>
        <Input
          placeholder={modelPlaceholder[provider] || 'text-embedding-3-large'}
          value={documentModel.model || ''}
          onChange={(event) =>
            onChange({
              ...config,
              embedding: {
                ...embedding,
                document_model: { ...documentModel, model: event.target.value },
                query_model: { ...documentModel, model: event.target.value },
              },
            })
          }
        />
      </div>
      {provider !== 'ollama' && (
        <div>
          <p className="text-sm font-semibold">API key</p>
          <Input
            placeholder="sk-..."
            value={documentModel.api_key || ''}
            onChange={(event) =>
              onChange({
                ...config,
                embedding: {
                  ...embedding,
                  document_model: { ...documentModel, api_key: event.target.value },
                  query_model: { ...documentModel, api_key: event.target.value },
                },
              })
            }
          />
        </div>
      )}
    </div>
  );
}
