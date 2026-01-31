import { FieldLabel } from '@/components/ui/field-label';
import { NumberInput } from '@/components/ui/number-input';
import { Select } from '@/components/ui/select';
import { ToggleSwitch } from '@/components/ui/toggle-switch';

interface SectionProps {
  config: any;
  onChange: (value: any) => void;
}

export function ConversationConfigSection({ config, onChange }: SectionProps) {
  const conversation = config?.conversation || {};
  const memory = conversation.memory || {};
  const persistence = conversation.persistence || {};

  const updateConversation = (nextConversation: any) => {
    onChange({ ...config, conversation: nextConversation });
  };

  return (
    <div className="space-y-8">
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-ink">Memory</h3>
        <div>
          <FieldLabel label="Enabled" help="Active la memoire de conversation." />
          <ToggleSwitch
            checked={memory.enabled ?? true}
            onChange={(checked) => updateConversation({ ...conversation, memory: { ...memory, enabled: checked } })}
          />
        </div>
        <div>
          <FieldLabel label="Type" help="buffer_window : garde les N derniers messages. summary : resume. none : pas de memoire." />
          <Select
            value={memory.type || 'buffer_window'}
            onChange={(event) => updateConversation({ ...conversation, memory: { ...memory, type: event.target.value } })}
          >
            <option value="buffer_window">Buffer window</option>
            <option value="summary">Summary</option>
            <option value="none">None</option>
          </Select>
        </div>
        {memory.type === 'buffer_window' ? (
          <div>
            <FieldLabel label="Window size" help="Nombre de messages precedents gardes en memoire." />
            <NumberInput
              value={memory.window_size ?? 10}
              min={1}
              max={50}
              step={1}
              onChange={(value) =>
                updateConversation({ ...conversation, memory: { ...memory, window_size: value ?? 10 } })
              }
            />
          </div>
        ) : null}
        <div>
          <FieldLabel label="Include in prompt" help="Inclure l'historique dans le prompt." />
          <ToggleSwitch
            checked={memory.include_in_prompt ?? true}
            onChange={(checked) =>
              updateConversation({ ...conversation, memory: { ...memory, include_in_prompt: checked } })
            }
          />
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-ink">Persistence</h3>
        <div>
          <FieldLabel label="Enabled" help="Sauvegarder les conversations entre les redemarrages." />
          <ToggleSwitch
            checked={persistence.enabled ?? false}
            onChange={(checked) =>
              updateConversation({ ...conversation, persistence: { ...persistence, enabled: checked } })
            }
          />
        </div>
        <div>
          <FieldLabel label="Backend" help="Backend de persistance." />
          <Select
            value={persistence.backend || 'memory'}
            onChange={(event) =>
              updateConversation({ ...conversation, persistence: { ...persistence, backend: event.target.value } })
            }
          >
            <option value="memory">Memory</option>
            <option value="redis">Redis</option>
            <option value="postgresql">PostgreSQL</option>
          </Select>
        </div>
      </div>
    </div>
  );
}
