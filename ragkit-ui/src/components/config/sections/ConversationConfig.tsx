import { useTranslation } from 'react-i18next';
import { FieldLabel } from '@/components/ui/field-label';
import { NumberInput } from '@/components/ui/number-input';
import { Select } from '@/components/ui/select';
import { ToggleSwitch } from '@/components/ui/toggle-switch';

interface SectionProps {
  config: any;
  onChange: (value: any) => void;
}

export function ConversationConfigSection({ config, onChange }: SectionProps) {
  const { t } = useTranslation();
  const conversation = config?.conversation || {};
  const memory = conversation.memory || {};
  const persistence = conversation.persistence || {};

  const updateConversation = (nextConversation: any) => {
    onChange({ ...config, conversation: nextConversation });
  };

  return (
    <div className="space-y-8">
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-ink">{t('config.conversation.memoryTitle')}</h3>
        <div>
          <FieldLabel label={t('wizard.retrieval.enabledLabel')} help={t('config.conversation.memoryEnabledHelp')} />
          <ToggleSwitch
            checked={memory.enabled ?? true}
            onChange={(checked) => updateConversation({ ...conversation, memory: { ...memory, enabled: checked } })}
          />
        </div>
        <div>
          <FieldLabel label={t('config.conversation.memoryTypeLabel')} help={t('config.conversation.memoryTypeHelp')} />
          <Select
            value={memory.type || 'buffer_window'}
            onChange={(event) => updateConversation({ ...conversation, memory: { ...memory, type: event.target.value } })}
          >
            <option value="buffer_window">{t('config.conversation.bufferWindow')}</option>
            <option value="summary">{t('config.conversation.summary')}</option>
            <option value="none">{t('common.options.none')}</option>
          </Select>
        </div>
        {memory.type === 'buffer_window' ? (
          <div>
            <FieldLabel label={t('config.conversation.windowLabel')} help={t('config.conversation.windowHelp')} />
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
          <FieldLabel label={t('config.conversation.includeLabel')} help={t('config.conversation.includeHelp')} />
          <ToggleSwitch
            checked={memory.include_in_prompt ?? true}
            onChange={(checked) =>
              updateConversation({ ...conversation, memory: { ...memory, include_in_prompt: checked } })
            }
          />
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-ink">{t('config.conversation.persistenceTitle')}</h3>
        <div>
          <FieldLabel label={t('wizard.retrieval.enabledLabel')} help={t('config.conversation.persistenceEnabledHelp')} />
          <ToggleSwitch
            checked={persistence.enabled ?? false}
            onChange={(checked) =>
              updateConversation({ ...conversation, persistence: { ...persistence, enabled: checked } })
            }
          />
        </div>
        <div>
          <FieldLabel label={t('config.conversation.backendLabel')} help={t('config.conversation.backendHelp')} />
          <Select
            value={persistence.backend || 'memory'}
            onChange={(event) =>
              updateConversation({ ...conversation, persistence: { ...persistence, backend: event.target.value } })
            }
          >
            <option value="memory">{t('common.cache.memory')}</option>
            <option value="redis">Redis</option>
            <option value="postgresql">PostgreSQL</option>
          </Select>
        </div>
      </div>
    </div>
  );
}
