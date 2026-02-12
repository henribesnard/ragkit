import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ChatContainer } from '@/components/chatbot/ChatContainer';
import { DebugPanel } from '@/components/chatbot/DebugPanel';
import { queryRag, queryRagStream } from '@/api/query';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: Array<string | Record<string, any>>;
  isStreaming?: boolean;
  debug?: {
    intent?: string;
    latency_ms?: number;
    chunks_retrieved?: number;
    needs_retrieval?: boolean;
    detected_language?: string;
    response_language?: string;
    streaming?: boolean;
  };
}

export function Chatbot() {
  const { t } = useTranslation();
  const [messages, setMessages] = useState<Message[]>([]);
  const [showDebug, setShowDebug] = useState(true);
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = async (query: string) => {
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: query,
    };
    const assistantId = crypto.randomUUID();
    const history = messages;

    setMessages((prev) => [
      ...prev,
      userMessage,
      { id: assistantId, role: 'assistant', content: '', isStreaming: true },
    ]);
    setIsLoading(true);

    const start = performance.now();

    const updateAssistant = (updater: (message: Message) => Message) => {
      setMessages((prev) => prev.map((message) => (message.id === assistantId ? updater(message) : message)));
    };

    const finalizeMessage = (response: any, streaming: boolean) => {
      const latency = performance.now() - start;
      const metadata = response?.metadata || {};
      const content = response?.content ?? response?.answer ?? '';
      updateAssistant((message) => ({
        ...message,
        content,
        sources: response?.sources || [],
        isStreaming: false,
        debug: {
          intent: metadata.intent,
          latency_ms: latency,
          chunks_retrieved: metadata.chunks_count || 0,
          needs_retrieval: metadata.needs_retrieval ?? true,
          detected_language: metadata.detected_language,
          response_language: metadata.response_language,
          streaming,
        },
      }));
    };

    try {
      await queryRagStream(
        { query, history },
        {
          onDelta: (content) => {
            updateAssistant((message) => ({
              ...message,
              content: message.content + content,
              isStreaming: true,
            }));
          },
          onFinal: (response) => {
            finalizeMessage(response, true);
          },
          onError: () => {
            // handled in catch
          },
        }
      );
    } catch (error) {
      const err = error as Error;
      if (err.message === 'STREAMING_DISABLED') {
        try {
          const response = await queryRag({ query, history });
          finalizeMessage(response, false);
        } catch {
          updateAssistant((message) => ({
            ...message,
            isStreaming: false,
            content: t('chat.errors.streamingDisabled'),
          }));
        }
      } else {
        updateAssistant((message) => ({
          ...message,
          isStreaming: false,
          content: t('chat.errors.unreachable'),
        }));
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-12rem)] gap-6">
      <div className="flex-1">
        <ChatContainer messages={messages} onSend={handleSend} isLoading={isLoading} />
      </div>
      {showDebug && (
        <div className="w-80">
          <DebugPanel lastMessage={messages[messages.length - 1]} onClose={() => setShowDebug(false)} />
        </div>
      )}
    </div>
  );
}
