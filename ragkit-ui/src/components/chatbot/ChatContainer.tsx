import { useTranslation } from 'react-i18next';
import { ChatInput } from './ChatInput';
import { ChatMessage } from './ChatMessage';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: Array<string | Record<string, any>>;
  isStreaming?: boolean;
}

interface ChatContainerProps {
  messages: Message[];
  onSend: (message: string) => void;
  isLoading?: boolean;
}

export function ChatContainer({ messages, onSend, isLoading }: ChatContainerProps) {
  const { t } = useTranslation();
  return (
    <div className="flex h-full flex-col gap-6">
      <div className="flex-1 space-y-4 overflow-y-auto rounded-3xl bg-white/50 p-6">
        {messages.length === 0 ? (
          <p className="text-sm text-muted">{t('chat.empty')}</p>
        ) : (
          messages.map((message) => <ChatMessage key={message.id} {...message} />)
        )}
      </div>
      <ChatInput onSend={onSend} isLoading={isLoading} />
    </div>
  );
}
