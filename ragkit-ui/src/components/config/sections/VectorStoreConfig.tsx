import { useTranslation } from 'react-i18next';
import { FieldLabel } from '@/components/ui/field-label';
import { Input } from '@/components/ui/input';
import { NumberInput } from '@/components/ui/number-input';
import { Select } from '@/components/ui/select';

interface SectionProps {
  config: any;
  onChange: (value: any) => void;
}

export function VectorStoreConfigSection({ config, onChange }: SectionProps) {
  const { t } = useTranslation();
  const vectorStore = config?.vector_store || {};
  const qdrant = vectorStore.qdrant || {};
  const chroma = vectorStore.chroma || {};

  const updateVectorStore = (nextVectorStore: any) => {
    onChange({ ...config, vector_store: nextVectorStore });
  };

  return (
    <div className="space-y-6">
      <div>
        <FieldLabel
          label={t('wizard.embedding.providerLabel')}
          help={t('config.vectorStore.providerHelp')}
        />
        <Select
          value={vectorStore.provider || 'qdrant'}
          onChange={(event) => updateVectorStore({ ...vectorStore, provider: event.target.value })}
        >
          <option value="qdrant">Qdrant</option>
          <option value="chroma">Chroma</option>
        </Select>
      </div>

      {vectorStore.provider === 'qdrant' ? (
        <div className="space-y-4">
          <div>
            <FieldLabel label={t('config.vectorStore.modeLabel')} help={t('config.vectorStore.qdrantModeHelp')} />
            <Select
              value={qdrant.mode || 'memory'}
              onChange={(event) => updateVectorStore({ ...vectorStore, qdrant: { ...qdrant, mode: event.target.value } })}
            >
              <option value="memory">{t('common.cache.memory')}</option>
              <option value="local">{t('common.options.local')}</option>
              <option value="cloud">{t('common.options.cloud')}</option>
            </Select>
          </div>
          {qdrant.mode === 'local' ? (
            <div>
              <FieldLabel label={t('wizard.sources.pathLabel')} help={t('config.vectorStore.qdrantPathHelp')} />
              <Input
                value={qdrant.path || ''}
                onChange={(event) => updateVectorStore({ ...vectorStore, qdrant: { ...qdrant, path: event.target.value } })}
              />
            </div>
          ) : null}
          {qdrant.mode === 'cloud' ? (
            <>
              <div>
                <FieldLabel label={t('config.vectorStore.urlLabel')} help={t('config.vectorStore.qdrantUrlHelp')} />
                <Input
                  value={qdrant.url || ''}
                  onChange={(event) => updateVectorStore({ ...vectorStore, qdrant: { ...qdrant, url: event.target.value } })}
                />
              </div>
              <div>
                <FieldLabel label={t('wizard.embedding.apiKeyLabel')} help={t('config.vectorStore.qdrantApiKeyHelp')} />
                <Input
                  type="password"
                  value={qdrant.api_key || ''}
                  onChange={(event) => updateVectorStore({ ...vectorStore, qdrant: { ...qdrant, api_key: event.target.value } })}
                />
              </div>
            </>
          ) : null}
          <div>
            <FieldLabel label={t('config.vectorStore.collectionLabel')} help={t('config.vectorStore.collectionHelp')} />
            <Input
              value={qdrant.collection_name || ''}
              onChange={(event) =>
                updateVectorStore({ ...vectorStore, qdrant: { ...qdrant, collection_name: event.target.value } })
              }
            />
          </div>
          <div>
            <FieldLabel label={t('config.vectorStore.distanceLabel')} help={t('config.vectorStore.distanceHelp')} />
            <Select
              value={qdrant.distance_metric || 'cosine'}
              onChange={(event) =>
                updateVectorStore({ ...vectorStore, qdrant: { ...qdrant, distance_metric: event.target.value } })
              }
            >
              <option value="cosine">Cosine</option>
              <option value="euclidean">Euclidean</option>
              <option value="dot">Dot</option>
            </Select>
          </div>
          <div>
            <FieldLabel label={t('config.vectorStore.batchLabel')} help={t('config.vectorStore.batchHelp')} />
            <NumberInput
              value={qdrant.add_batch_size ?? null}
              min={1}
              max={10000}
              step={1}
              onChange={(value) =>
                updateVectorStore({ ...vectorStore, qdrant: { ...qdrant, add_batch_size: value } })
              }
            />
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div>
            <FieldLabel label={t('config.vectorStore.modeLabel')} help={t('config.vectorStore.chromaModeHelp')} />
            <Select
              value={chroma.mode || 'memory'}
              onChange={(event) => updateVectorStore({ ...vectorStore, chroma: { ...chroma, mode: event.target.value } })}
            >
              <option value="memory">{t('common.cache.memory')}</option>
              <option value="persistent">{t('common.options.persistent')}</option>
            </Select>
          </div>
          {chroma.mode === 'persistent' ? (
            <div>
              <FieldLabel label={t('wizard.sources.pathLabel')} help={t('config.vectorStore.chromaPathHelp')} />
              <Input
                value={chroma.path || ''}
                onChange={(event) => updateVectorStore({ ...vectorStore, chroma: { ...chroma, path: event.target.value } })}
              />
            </div>
          ) : null}
          <div>
            <FieldLabel label={t('config.vectorStore.collectionLabel')} help={t('config.vectorStore.chromaCollectionHelp')} />
            <Input
              value={chroma.collection_name || ''}
              onChange={(event) =>
                updateVectorStore({ ...vectorStore, chroma: { ...chroma, collection_name: event.target.value } })
              }
            />
          </div>
          <div>
            <FieldLabel label={t('config.vectorStore.batchLabel')} help={t('config.vectorStore.chromaBatchHelp')} />
            <NumberInput
              value={chroma.add_batch_size ?? 100}
              min={1}
              max={10000}
              step={1}
              onChange={(value) =>
                updateVectorStore({ ...vectorStore, chroma: { ...chroma, add_batch_size: value } })
              }
            />
          </div>
        </div>
      )}
    </div>
  );
}
