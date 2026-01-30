import { useState } from 'react';
import { ChatContainer } from '@/components/chatbot/ChatContainer';
import { DebugPanel } from '@/components/chatbot/DebugPanel';
import { queryRag } from '@/api/query';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
  debug?: {
    intent?: string;
    latency_ms?: number;
    chunks_retrieved?: number;
    needs_retrieval?: boolean;
  };
}

export function Chatbot() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [showDebug, setShowDebug] = useState(true);
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = async (query: string) => {
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: query,
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const start = performance.now();
      const response = await queryRag({ query, history: messages });
      const latency = performance.now() - start;

      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        debug: {
          intent: response.metadata?.intent,
          latency_ms: latency,
          chunks_retrieved: response.metadata?.chunks_count || 0,
          needs_retrieval: response.metadata?.needs_retrieval ?? true,
        },
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: 'Unable to reach the API. Please check the server logs.',
        },
      ]);
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
