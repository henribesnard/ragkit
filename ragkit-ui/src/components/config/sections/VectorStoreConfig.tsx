import { FieldLabel } from '@/components/ui/field-label';
import { Input } from '@/components/ui/input';
import { NumberInput } from '@/components/ui/number-input';
import { Select } from '@/components/ui/select';

interface SectionProps {
  config: any;
  onChange: (value: any) => void;
}

export function VectorStoreConfigSection({ config, onChange }: SectionProps) {
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
          label="Provider"
          help="Base de donnees vectorielle. qdrant : performant, supporte le cloud. chroma : simple, bon pour le developpement."
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
            <FieldLabel label="Mode" help="memory : rapide, perdu au redemarrage. local : persiste sur disque. cloud : heberge sur Qdrant Cloud." />
            <Select
              value={qdrant.mode || 'memory'}
              onChange={(event) => updateVectorStore({ ...vectorStore, qdrant: { ...qdrant, mode: event.target.value } })}
            >
              <option value="memory">Memory</option>
              <option value="local">Local</option>
              <option value="cloud">Cloud</option>
            </Select>
          </div>
          {qdrant.mode === 'local' ? (
            <div>
              <FieldLabel label="Path" help="Chemin du stockage local Qdrant." />
              <Input
                value={qdrant.path || ''}
                onChange={(event) => updateVectorStore({ ...vectorStore, qdrant: { ...qdrant, path: event.target.value } })}
              />
            </div>
          ) : null}
          {qdrant.mode === 'cloud' ? (
            <>
              <div>
                <FieldLabel label="URL" help="URL du cluster Qdrant Cloud." />
                <Input
                  value={qdrant.url || ''}
                  onChange={(event) => updateVectorStore({ ...vectorStore, qdrant: { ...qdrant, url: event.target.value } })}
                />
              </div>
              <div>
                <FieldLabel label="API key" help="Cle API Qdrant Cloud." />
                <Input
                  type="password"
                  value={qdrant.api_key || ''}
                  onChange={(event) => updateVectorStore({ ...vectorStore, qdrant: { ...qdrant, api_key: event.target.value } })}
                />
              </div>
            </>
          ) : null}
          <div>
            <FieldLabel label="Collection name" help="Nom de la collection dans la base vectorielle." />
            <Input
              value={qdrant.collection_name || ''}
              onChange={(event) =>
                updateVectorStore({ ...vectorStore, qdrant: { ...qdrant, collection_name: event.target.value } })
              }
            />
          </div>
          <div>
            <FieldLabel label="Distance metric" help="Methode de calcul de distance entre vecteurs." />
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
            <FieldLabel label="Add batch size" help="Taille des lots pour les insertions (laisser vide = pas de batching)." />
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
            <FieldLabel label="Mode" help="memory : rapide, perdu au redemarrage. persistent : persiste sur disque." />
            <Select
              value={chroma.mode || 'memory'}
              onChange={(event) => updateVectorStore({ ...vectorStore, chroma: { ...chroma, mode: event.target.value } })}
            >
              <option value="memory">Memory</option>
              <option value="persistent">Persistent</option>
            </Select>
          </div>
          {chroma.mode === 'persistent' ? (
            <div>
              <FieldLabel label="Path" help="Chemin du stockage Chroma persistant." />
              <Input
                value={chroma.path || ''}
                onChange={(event) => updateVectorStore({ ...vectorStore, chroma: { ...chroma, path: event.target.value } })}
              />
            </div>
          ) : null}
          <div>
            <FieldLabel label="Collection name" help="Nom de la collection dans Chroma." />
            <Input
              value={chroma.collection_name || ''}
              onChange={(event) =>
                updateVectorStore({ ...vectorStore, chroma: { ...chroma, collection_name: event.target.value } })
              }
            />
          </div>
          <div>
            <FieldLabel label="Add batch size" help="Taille des lots pour les insertions." />
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
