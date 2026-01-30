import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';

interface SectionProps {
  config: any;
  onChange: (value: any) => void;
}

export function RetrievalConfigSection({ config, onChange }: SectionProps) {
  const retrieval = config?.retrieval || {};
  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold">Architecture</p>
        <Select
          value={retrieval.architecture || 'semantic'}
          onChange={(event) => onChange({ ...config, retrieval: { ...retrieval, architecture: event.target.value } })}
        >
          <option value="semantic">Semantic</option>
          <option value="lexical">Lexical</option>
          <option value="hybrid">Hybrid</option>
          <option value="hybrid_rerank">Hybrid + Rerank</option>
        </Select>
      </div>
      <div>
        <p className="text-sm font-semibold">Top K</p>
        <Input
          type="number"
          value={retrieval.semantic?.top_k || 5}
          onChange={(event) =>
            onChange({
              ...config,
              retrieval: {
                ...retrieval,
                semantic: { ...(retrieval.semantic || {}), top_k: Number(event.target.value) },
              },
            })
          }
        />
      </div>
    </div>
  );
}
