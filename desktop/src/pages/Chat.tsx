import { useState, useRef, useEffect, useMemo, useCallback, memo } from "react";
import { useTranslation } from "react-i18next";
import { useParams } from "react-router-dom";
import { Send, FileText, ChevronDown, ChevronUp, MessageSquare, Database, Copy, Check } from "lucide-react";
import { ipc, Message, Source, KnowledgeBase } from "../lib/ipc";
import { Button, Select, Card, Textarea, type SelectOption } from "../components/ui";
import { cn } from "../lib/utils";
import { parseError } from "../lib/errors";

export function Chat() {
  const { t } = useTranslation();
  const { conversationId } = useParams();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [selectedKb, setSelectedKb] = useState<string>("");
  const [currentConvId, setCurrentConvId] = useState<string | null>(
    conversationId || null
  );
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Load knowledge bases on mount
  useEffect(() => {
    ipc.listKnowledgeBases().then(setKnowledgeBases).catch(console.error);
  }, []);

  // Load conversation messages
  useEffect(() => {
    if (conversationId) {
      setCurrentConvId(conversationId);
      ipc.getMessages(conversationId).then(setMessages).catch(console.error);
    }
  }, [conversationId]);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Focus input when KB is selected
  useEffect(() => {
    if (selectedKb && inputRef.current) {
      inputRef.current.focus();
    }
  }, [selectedKb]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const question = input.trim();
    setInput("");
    setIsLoading(true);

    try {
      // Create conversation if needed
      let convId = currentConvId;
      if (!convId) {
        const conv = await ipc.createConversation(selectedKb || undefined);
        convId = conv.id;
        setCurrentConvId(convId);
      }

      // Add user message optimistically
      const userMessage: Message = {
        id: `temp-${Date.now()}`,
        conversation_id: convId,
        role: "user",
        content: question,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);

      // Send query
      const response = await ipc.query({
        kbId: selectedKb || "",
        conversationId: convId,
        question,
      });

      // Add assistant message
      const assistantMessage: Message = {
        id: `temp-${Date.now() + 1}`,
        conversation_id: convId,
        role: "assistant",
        content: response.answer,
        sources: response.sources,
        latency_ms: response.latency_ms,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Query failed:", error);
      // Parse error for user-friendly message
      const errorInfo = parseError(error);
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        conversation_id: currentConvId || "",
        role: "assistant",
        content: `**${errorInfo.title}**\n\n${errorInfo.message}${errorInfo.suggestion ? `\n\n💡 ${errorInfo.suggestion}` : ""
          }`,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Convert knowledge bases to select options (memoized)
  const kbOptions = useMemo<SelectOption[]>(
    () => knowledgeBases.map((kb) => ({ value: kb.id, label: kb.name })),
    [knowledgeBases]
  );

  // Memoized KB change handler
  const handleKbChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedKb(e.target.value);
  }, []);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
            <MessageSquare className="w-5 h-5 text-primary-600 dark:text-primary-400" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
              {t("chat.title")}
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {t("chat.messageCount", { count: messages.length })}
            </p>
          </div>
        </div>
        <div className="w-64">
          <Select
            options={kbOptions}
            value={selectedKb}
            onChange={handleKbChange}
            placeholder={t("chat.selectKnowledgeBase")}
          />
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin">
        {messages.length === 0 ? (
          <EmptyState hasKnowledgeBase={!!selectedKb} />
        ) : (
          messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))
        )}
        {isLoading && <TypingIndicator />}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form
        onSubmit={handleSubmit}
        className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800"
      >
        <div className="flex items-center gap-3">
          <div className="flex-1">
            <div className="flex-1">
              <Textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={
                  selectedKb ? t("chat.askPlaceholder") : t("chat.selectFirst")
                }
                disabled={!selectedKb || isLoading}
                className="min-h-[44px] max-h-[200px] resize-none py-3"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
              />
            </div>
          </div>
          <Button
            type="submit"
            disabled={!input.trim() || isLoading || !selectedKb}
            isLoading={isLoading}
            size="icon"
          >
            <Send className="w-5 h-5" />
          </Button>
        </div>
      </form>
    </div>
  );
}

// Empty state component (memoized)
const EmptyState = memo(function EmptyState({ hasKnowledgeBase }: { hasKnowledgeBase: boolean }) {
  const { t } = useTranslation();
  return (
    <div className="flex flex-col items-center justify-center h-full text-center">
      <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary-100 to-primary-200 dark:from-primary-900/30 dark:to-primary-800/30 flex items-center justify-center mb-6 shadow-lg">
        {hasKnowledgeBase ? (
          <MessageSquare className="w-10 h-10 text-primary-600 dark:text-primary-400" />
        ) : (
          <Database className="w-10 h-10 text-primary-600 dark:text-primary-400" />
        )}
      </div>
      <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">
        {hasKnowledgeBase ? t("chat.empty.startTitle") : t("chat.empty.selectTitle")}
      </h2>
      <p className="mt-3 text-gray-600 dark:text-gray-400 max-w-md text-lg">
        {hasKnowledgeBase
          ? t("chat.empty.startDescription")
          : t("chat.empty.selectDescription")}
      </p>
    </div>
  );
});

// Typing indicator component (memoized - no props)
const TypingIndicator = memo(function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="bg-gray-100 dark:bg-gray-700 rounded-2xl px-4 py-3">
        <div className="flex items-center gap-1">
          <div
            className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce"
            style={{ animationDelay: "0ms" }}
          />
          <div
            className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce"
            style={{ animationDelay: "150ms" }}
          />
          <div
            className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce"
            style={{ animationDelay: "300ms" }}
          />
        </div>
      </div>
    </div>
  );
});

// Message bubble component (memoized)
const MessageBubble = memo(function MessageBubble({ message }: { message: Message }) {
  const { t } = useTranslation();
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const isUser = message.role === "user";

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  return (
    <div
      className={cn(
        "flex animate-in fade-in-0 slide-in-from-bottom-2 duration-300 group",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      <div
        className={cn(
          "max-w-[80%] rounded-2xl px-4 py-3 relative",
          isUser
            ? "bg-primary-600 text-white"
            : "bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white"
        )}
      >
        {!isUser && (
          <button
            onClick={handleCopy}
            className="absolute top-2 right-2 p-1.5 rounded-lg text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-gray-200 dark:hover:bg-gray-600"
            title={t("chat.copy")}
          >
            {copied ? (
              <Check className="w-3.5 h-3.5 text-green-500" />
            ) : (
              <Copy className="w-3.5 h-3.5" />
            )}
          </button>
        )}
        <div className="whitespace-pre-wrap leading-relaxed pr-6">{message.content}</div>

        {/* Sources */}
        {message.sources && message.sources.length > 0 && (
          <div className="mt-3 pt-3 border-t border-gray-200/30 dark:border-gray-600/50">
            <button
              onClick={() => setSourcesOpen(!sourcesOpen)}
              className={cn(
                "flex items-center text-sm transition-colors",
                isUser
                  ? "text-white/80 hover:text-white"
                  : "text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-white"
              )}
            >
              <FileText className="w-4 h-4 mr-1.5" />
              {t("chat.sources", { count: message.sources.length })}
              {sourcesOpen ? (
                <ChevronUp className="w-4 h-4 ml-1" />
              ) : (
                <ChevronDown className="w-4 h-4 ml-1" />
              )}
            </button>
            {sourcesOpen && (
              <div className="mt-3 space-y-2">
                {message.sources.map((source, i) => (
                  <SourceCard key={i} source={source} isUserMessage={isUser} />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Latency */}
        {message.latency_ms && (
          <p
            className={cn(
              "mt-2 text-xs",
              isUser ? "text-white/60" : "text-gray-500 dark:text-gray-400"
            )}
          >
            {message.latency_ms}ms
          </p>
        )}
      </div>
    </div>
  );
});

// Source card component (memoized)
const SourceCard = memo(function SourceCard({
  source,
  isUserMessage,
}: {
  source: Source;
  isUserMessage: boolean;
}) {
  const { t } = useTranslation();
  return (
    <Card
      variant="outlined"
      className={cn(
        "p-3",
        isUserMessage
          ? "border-white/20 bg-white/10"
          : "border-gray-200 dark:border-gray-600 bg-white/50 dark:bg-black/20"
      )}
    >
      <div className="flex items-start gap-2">
        <FileText
          className={cn(
            "w-4 h-4 mt-0.5 flex-shrink-0",
            isUserMessage ? "text-white/70" : "text-gray-500 dark:text-gray-400"
          )}
        />
        <div className="flex-1 min-w-0">
          <p
            className={cn(
              "font-medium text-sm truncate",
              isUserMessage ? "text-white" : "text-gray-800 dark:text-gray-200"
            )}
          >
            {source.filename}
          </p>
          <p
            className={cn(
              "mt-1 text-sm line-clamp-2",
              isUserMessage ? "text-white/80" : "text-gray-600 dark:text-gray-400"
            )}
          >
            {source.chunk}
          </p>
          <div
            className={cn(
              "mt-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium",
              source.score >= 0.8
                ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                : source.score >= 0.5
                  ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400"
                  : "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400"
            )}
          >
            {t("chat.match", { score: Math.round(source.score * 100) })}
          </div>
        </div>
      </div>
    </Card>
  );
});
