import { useState, useEffect } from "react";
import {
  Save,
  Key,
  Cpu,
  MessageSquare,
  Loader2,
  Check,
  X,
  Settings2,
  ShieldCheck,
  SlidersHorizontal,
  Search,
} from "lucide-react";
import { ipc, Settings as SettingsType } from "../lib/ipc";
import { OllamaStatusCard } from "../components/OllamaStatus";
import {
  Button,
  Select,
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  Modal,
  ModalFooter,
  Input,
  useToast,
  useConfirm,
  type SelectOption,
} from "../components/ui";
import { cn } from "../lib/utils";

// Provider options
const EMBEDDING_PROVIDERS: SelectOption[] = [
  { value: "onnx_local", label: "ONNX Local (Offline)" },
  { value: "openai", label: "OpenAI" },
  { value: "cohere", label: "Cohere" },
  { value: "ollama", label: "Ollama" },
];

const EMBEDDING_MODELS: Record<string, SelectOption[]> = {
  onnx_local: [
    { value: "all-MiniLM-L6-v2", label: "all-MiniLM-L6-v2 (Fast, 384 dim)" },
    { value: "all-mpnet-base-v2", label: "all-mpnet-base-v2 (Quality, 768 dim)" },
    { value: "multilingual-e5-small", label: "multilingual-e5-small (Multilingual)" },
  ],
  openai: [
    { value: "text-embedding-3-small", label: "text-embedding-3-small" },
    { value: "text-embedding-3-large", label: "text-embedding-3-large" },
  ],
  cohere: [
    { value: "embed-english-v3.0", label: "embed-english-v3.0" },
    { value: "embed-multilingual-v3.0", label: "embed-multilingual-v3.0" },
  ],
  ollama: [
    { value: "nomic-embed-text", label: "nomic-embed-text" },
    { value: "mxbai-embed-large", label: "mxbai-embed-large" },
  ],
};

const LLM_PROVIDERS: SelectOption[] = [
  { value: "ollama", label: "Ollama (Local)" },
  { value: "openai", label: "OpenAI" },
  { value: "anthropic", label: "Anthropic" },
  { value: "deepseek", label: "DeepSeek" },
  { value: "groq", label: "Groq" },
  { value: "mistral", label: "Mistral" },
  { value: "gemini", label: "Gemini" },
];

const LLM_MODELS: Record<string, SelectOption[]> = {
  ollama: [
    { value: "llama3.2:3b", label: "Llama 3.2 3B (Fast)" },
    { value: "llama3.1:8b", label: "Llama 3.1 8B (Quality)" },
    { value: "mistral:7b", label: "Mistral 7B" },
  ],
  openai: [
    { value: "gpt-4o-mini", label: "GPT-4o Mini" },
    { value: "gpt-4o", label: "GPT-4o" },
  ],
  anthropic: [
    { value: "claude-3-haiku-20240307", label: "Claude 3 Haiku" },
    { value: "claude-3-5-sonnet-20241022", label: "Claude 3.5 Sonnet" },
  ],
  deepseek: [
    { value: "deepseek-chat", label: "DeepSeek Chat" },
    { value: "deepseek-reasoner", label: "DeepSeek Reasoner" },
  ],
  groq: [
    { value: "llama-3.1-8b-instant", label: "Llama 3.1 8B Instant" },
    { value: "llama-3.1-70b-versatile", label: "Llama 3.1 70B Versatile" },
    { value: "mixtral-8x7b-32768", label: "Mixtral 8x7B 32K" },
  ],
  mistral: [
    { value: "mistral-small-latest", label: "Mistral Small (Latest)" },
    { value: "mistral-large-latest", label: "Mistral Large (Latest)" },
    { value: "codestral-latest", label: "Codestral (Latest)" },
  ],
  gemini: [
    { value: "gemini-1.5-flash", label: "Gemini 1.5 Flash" },
    { value: "gemini-1.5-pro", label: "Gemini 1.5 Pro" },
  ],
};

const API_KEY_PROVIDERS = [
  { id: "openai", name: "OpenAI", description: "For GPT models and embeddings" },
  { id: "anthropic", name: "Anthropic", description: "For Claude models" },
  { id: "deepseek", name: "DeepSeek", description: "For DeepSeek models" },
  { id: "groq", name: "Groq", description: "For Groq-hosted models" },
  { id: "mistral", name: "Mistral", description: "For Mistral models" },
  { id: "gemini", name: "Gemini", description: "For Google Gemini models" },
  { id: "cohere", name: "Cohere", description: "For Cohere models" },
];

const CHUNKING_STRATEGIES: SelectOption[] = [
  { value: "fixed", label: "Fixed" },
  { value: "semantic", label: "Semantic (Experimental)" },
];

const RETRIEVAL_ARCHITECTURES: SelectOption[] = [
  { value: "semantic", label: "Semantic" },
  { value: "lexical", label: "Lexical (BM25)" },
  { value: "hybrid", label: "Hybrid (Semantic + Lexical)" },
  { value: "hybrid_rerank", label: "Hybrid + Rerank" },
];

const RERANK_PROVIDERS: SelectOption[] = [
  { value: "none", label: "None" },
  { value: "cohere", label: "Cohere" },
];

export function Settings() {
  const toast = useToast();
  const confirm = useConfirm();
  const [settings, setSettings] = useState<SettingsType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [apiKeys, setApiKeys] = useState<Record<string, boolean>>({});
  const [showApiKeyModal, setShowApiKeyModal] = useState(false);
  const [currentProvider, setCurrentProvider] = useState<string | null>(null);
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [embeddingUseCustomModel, setEmbeddingUseCustomModel] = useState(false);
  const [embeddingCustomModel, setEmbeddingCustomModel] = useState("");
  const [embeddingListModel, setEmbeddingListModel] = useState("");
  const [llmUseCustomModel, setLlmUseCustomModel] = useState(false);
  const [llmCustomModel, setLlmCustomModel] = useState("");
  const [llmListModel, setLlmListModel] = useState("");

  // Load settings
  useEffect(() => {
    loadSettings();
  }, []);

  useEffect(() => {
    if (!settings) return;
    const models = EMBEDDING_MODELS[settings.embedding_provider] || [];
    const hasMatch = models.some((model) => model.value === settings.embedding_model);
    setEmbeddingUseCustomModel(!hasMatch);
    if (hasMatch) {
      setEmbeddingCustomModel("");
      setEmbeddingListModel(settings.embedding_model);
    } else {
      setEmbeddingCustomModel(settings.embedding_model);
      setEmbeddingListModel(models[0]?.value || "");
    }
  }, [settings?.embedding_provider]);

  useEffect(() => {
    if (!settings) return;
    const models = LLM_MODELS[settings.llm_provider] || [];
    const hasMatch = models.some((model) => model.value === settings.llm_model);
    setLlmUseCustomModel(!hasMatch);
    if (hasMatch) {
      setLlmCustomModel("");
      setLlmListModel(settings.llm_model);
    } else {
      setLlmCustomModel(settings.llm_model);
      setLlmListModel(models[0]?.value || "");
    }
  }, [settings?.llm_provider]);

  const loadSettings = async () => {
    try {
      setIsLoading(true);
      const s = await ipc.getSettings();
      setSettings(s);

      // Check API keys
      const keys: Record<string, boolean> = {};
      for (const provider of API_KEY_PROVIDERS) {
        keys[provider.id] = await ipc.hasApiKey(provider.id);
      }
      setApiKeys(keys);
    } catch (error) {
      console.error("Failed to load settings:", error);
      toast.error("Failed to load settings");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!settings) return;

    try {
      setIsSaving(true);
      await ipc.updateSettings(settings);
      toast.success("Settings saved", "Your changes have been applied.");
    } catch (error) {
      console.error("Failed to save settings:", error);
      toast.error("Failed to save settings");
    } finally {
      setIsSaving(false);
    }
  };

  const openApiKeyModal = (provider: string) => {
    setCurrentProvider(provider);
    setApiKeyInput("");
    setShowApiKeyModal(true);
  };

  const handleSetApiKey = async () => {
    if (!currentProvider || !apiKeyInput.trim()) return;

    try {
      await ipc.setApiKey(currentProvider, apiKeyInput.trim());
      setApiKeys((prev) => ({ ...prev, [currentProvider]: true }));
      setShowApiKeyModal(false);
      setApiKeyInput("");
      toast.success("API key saved", `${currentProvider} API key has been stored securely.`);
    } catch (error) {
      console.error("Failed to set API key:", error);
      toast.error("Failed to save API key");
    }
  };

  const handleDeleteApiKey = async (provider: string) => {
    const confirmed = await confirm({
      title: "Delete API Key",
      message: `Are you sure you want to delete the ${provider} API key? You will need to re-enter it to use this provider.`,
      confirmLabel: "Delete",
      cancelLabel: "Cancel",
      variant: "warning",
    });

    if (!confirmed) return;

    try {
      await ipc.deleteApiKey(provider);
      setApiKeys((prev) => ({ ...prev, [provider]: false }));
      toast.info("API key deleted", `${provider} API key has been removed.`);
    } catch (error) {
      console.error("Failed to delete API key:", error);
      toast.error("Failed to delete API key");
    }
  };

  if (isLoading || !settings) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <Loader2 className="w-10 h-10 text-primary-600 animate-spin" />
        <p className="mt-4 text-gray-500 dark:text-gray-400">Loading settings...</p>
      </div>
    );
  }

  const embeddingModels = EMBEDDING_MODELS[settings.embedding_provider] || [];
  const llmModels = LLM_MODELS[settings.llm_provider] || [];

  return (
    <div className="h-full overflow-auto">
      {/* Header */}
      <header className="sticky top-0 z-10 flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
            <Settings2 className="w-5 h-5 text-primary-600 dark:text-primary-400" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
              Settings
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Configure providers and models
            </p>
          </div>
        </div>
        <Button onClick={handleSave} isLoading={isSaving}>
          <Save className="w-4 h-4 mr-2" />
          Save
        </Button>
      </header>

      {/* Settings Sections */}
      <div className="p-6 max-w-3xl space-y-6">
        {/* Embedding Settings */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                <Cpu className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <CardTitle>Embedding Model</CardTitle>
                <CardDescription>
                  Choose how documents are converted to vectors for semantic search
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 sm:grid-cols-2">
              <Select
                label="Provider"
                options={EMBEDDING_PROVIDERS}
                value={settings.embedding_provider}
                onChange={(e) => {
                  const provider = e.target.value;
                  const nextModel = EMBEDDING_MODELS[provider]?.[0]?.value || "";
                  setEmbeddingListModel(nextModel);
                  setEmbeddingUseCustomModel(false);
                  setEmbeddingCustomModel("");
                  setSettings({
                    ...settings,
                    embedding_provider: provider,
                    embedding_model: nextModel,
                  });
                }}
              />
              {embeddingUseCustomModel ? (
                <Input
                  label="Custom Model"
                  value={embeddingCustomModel}
                  onChange={(e) => {
                    const value = e.target.value;
                    setEmbeddingCustomModel(value);
                    const fallback = embeddingListModel || embeddingModels[0]?.value || "";
                    setSettings({
                      ...settings,
                      embedding_model: value.trim() ? value : fallback,
                    });
                  }}
                  placeholder="e.g. text-embedding-3-small"
                />
              ) : (
                <Select
                  label="Model"
                  options={embeddingModels}
                  value={embeddingListModel || settings.embedding_model}
                  onChange={(e) => {
                    setEmbeddingListModel(e.target.value);
                    setSettings({ ...settings, embedding_model: e.target.value });
                  }}
                />
              )}
            </div>
            <div className="mt-2 flex justify-end">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  if (embeddingUseCustomModel) {
                    const fallback = embeddingListModel || embeddingModels[0]?.value || "";
                    setEmbeddingUseCustomModel(false);
                    setEmbeddingCustomModel("");
                    setSettings({ ...settings, embedding_model: fallback });
                  } else {
                    setEmbeddingUseCustomModel(true);
                    setEmbeddingCustomModel("");
                  }
                }}
              >
                {embeddingUseCustomModel ? "Use preset list" : "Use custom model"}
              </Button>
            </div>
            {settings.embedding_provider === "onnx_local" && (
              <p className="mt-3 text-sm text-green-600 dark:text-green-400 flex items-center gap-1">
                <ShieldCheck className="w-4 h-4" />
                Running locally - no API key required
              </p>
            )}
          </CardContent>
        </Card>

        {/* Chunking Settings */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center">
                <SlidersHorizontal className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
              </div>
              <div>
                <CardTitle>Chunking</CardTitle>
                <CardDescription>
                  Control how documents are split before embedding
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 sm:grid-cols-2">
              <Select
                label="Strategy"
                options={CHUNKING_STRATEGIES}
                value={settings.embedding_chunk_strategy}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    embedding_chunk_strategy: e.target.value,
                  })
                }
              />
              <Input
                type="number"
                label="Chunk size"
                min={50}
                max={2000}
                step={10}
                disabled={settings.embedding_chunk_strategy !== "fixed"}
                value={settings.embedding_chunk_size}
                onChange={(e) => {
                  const next = Number(e.target.value);
                  setSettings({
                    ...settings,
                    embedding_chunk_size: Number.isNaN(next)
                      ? settings.embedding_chunk_size
                      : next,
                  });
                }}
                hint="Larger chunks capture more context but reduce recall"
              />
              <Input
                type="number"
                label="Chunk overlap"
                min={0}
                max={500}
                step={5}
                disabled={settings.embedding_chunk_strategy !== "fixed"}
                value={settings.embedding_chunk_overlap}
                onChange={(e) => {
                  const next = Number(e.target.value);
                  setSettings({
                    ...settings,
                    embedding_chunk_overlap: Number.isNaN(next)
                      ? settings.embedding_chunk_overlap
                      : next,
                  });
                }}
                hint="Overlap helps preserve context between chunks"
              />
            </div>
          </CardContent>
        </Card>

        {/* Retrieval Settings */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
                <Search className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
              </div>
              <div>
                <CardTitle>Retrieval</CardTitle>
                <CardDescription>
                  Tune how documents are searched and ranked
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 sm:grid-cols-2">
              <Select
                label="Architecture"
                options={RETRIEVAL_ARCHITECTURES}
                value={settings.retrieval_architecture}
                onChange={(e) => {
                  const architecture = e.target.value;
                  setSettings({
                    ...settings,
                    retrieval_architecture: architecture,
                    retrieval_rerank_enabled:
                      architecture === "hybrid_rerank"
                        ? true
                        : settings.retrieval_rerank_enabled,
                  });
                }}
              />
              <Input
                type="number"
                label="Top K"
                min={1}
                max={50}
                step={1}
                value={settings.retrieval_top_k}
                onChange={(e) => {
                  const next = Number(e.target.value);
                  setSettings({
                    ...settings,
                    retrieval_top_k: Number.isNaN(next)
                      ? settings.retrieval_top_k
                      : next,
                  });
                }}
                hint="Number of candidates fetched per query"
              />
              <Input
                type="number"
                label="Semantic weight"
                min={0}
                max={1}
                step={0.05}
                disabled={settings.retrieval_architecture === "lexical"}
                value={settings.retrieval_semantic_weight}
                onChange={(e) => {
                  const next = Number(e.target.value);
                  setSettings({
                    ...settings,
                    retrieval_semantic_weight: Number.isNaN(next)
                      ? settings.retrieval_semantic_weight
                      : next,
                  });
                }}
              />
              <Input
                type="number"
                label="Lexical weight"
                min={0}
                max={1}
                step={0.05}
                disabled={settings.retrieval_architecture === "semantic"}
                value={settings.retrieval_lexical_weight}
                onChange={(e) => {
                  const next = Number(e.target.value);
                  setSettings({
                    ...settings,
                    retrieval_lexical_weight: Number.isNaN(next)
                      ? settings.retrieval_lexical_weight
                      : next,
                  });
                }}
              />
              <Input
                type="number"
                label="Rerank weight"
                min={0}
                max={1}
                step={0.05}
                value={settings.retrieval_rerank_weight}
                onChange={(e) => {
                  const next = Number(e.target.value);
                  setSettings({
                    ...settings,
                    retrieval_rerank_weight: Number.isNaN(next)
                      ? settings.retrieval_rerank_weight
                      : next,
                  });
                }}
              />
              <Input
                type="number"
                label="Max chunks"
                min={1}
                max={50}
                step={1}
                value={settings.retrieval_max_chunks}
                onChange={(e) => {
                  const next = Number(e.target.value);
                  setSettings({
                    ...settings,
                    retrieval_max_chunks: Number.isNaN(next)
                      ? settings.retrieval_max_chunks
                      : next,
                  });
                }}
                hint="Maximum chunks sent to the LLM"
              />
            </div>
            <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
              <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  checked={settings.retrieval_rerank_enabled}
                  disabled={settings.retrieval_architecture === "hybrid_rerank"}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      retrieval_rerank_enabled: e.target.checked,
                    })
                  }
                />
                Enable reranking
              </label>
              <div className="sm:w-56">
                <Select
                  label="Rerank provider"
                  options={RERANK_PROVIDERS}
                  value={settings.retrieval_rerank_provider}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      retrieval_rerank_provider: e.target.value,
                    })
                  }
                  disabled={!settings.retrieval_rerank_enabled}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* LLM Settings */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
                <MessageSquare className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <CardTitle>Language Model</CardTitle>
                <CardDescription>
                  Choose the AI model for generating responses
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 sm:grid-cols-2">
              <Select
                label="Provider"
                options={LLM_PROVIDERS}
                value={settings.llm_provider}
                onChange={(e) => {
                  const provider = e.target.value;
                  const nextModel = LLM_MODELS[provider]?.[0]?.value || "";
                  setLlmListModel(nextModel);
                  setLlmUseCustomModel(false);
                  setLlmCustomModel("");
                  setSettings({
                    ...settings,
                    llm_provider: provider,
                    llm_model: nextModel,
                  });
                }}
              />
              {llmUseCustomModel ? (
                <Input
                  label="Custom Model"
                  value={llmCustomModel}
                  onChange={(e) => {
                    const value = e.target.value;
                    setLlmCustomModel(value);
                    const fallback = llmListModel || llmModels[0]?.value || "";
                    setSettings({
                      ...settings,
                      llm_model: value.trim() ? value : fallback,
                    });
                  }}
                  placeholder="e.g. gpt-4o-mini"
                />
              ) : (
                <Select
                  label="Model"
                  options={llmModels}
                  value={llmListModel || settings.llm_model}
                  onChange={(e) => {
                    setLlmListModel(e.target.value);
                    setSettings({ ...settings, llm_model: e.target.value });
                  }}
                />
              )}
            </div>
            <div className="mt-2 flex justify-end">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  if (llmUseCustomModel) {
                    const fallback = llmListModel || llmModels[0]?.value || "";
                    setLlmUseCustomModel(false);
                    setLlmCustomModel("");
                    setSettings({ ...settings, llm_model: fallback });
                  } else {
                    setLlmUseCustomModel(true);
                    setLlmCustomModel("");
                  }
                }}
              >
                {llmUseCustomModel ? "Use preset list" : "Use custom model"}
              </Button>
            </div>
            {settings.llm_provider === "ollama" && (
              <p className="mt-3 text-sm text-green-600 dark:text-green-400 flex items-center gap-1">
                <ShieldCheck className="w-4 h-4" />
                Running locally - no API key required
              </p>
            )}
          </CardContent>
        </Card>

        {/* Ollama Status - Show when Ollama is selected */}
        {(settings.llm_provider === "ollama" || settings.embedding_provider === "ollama") && (
          <OllamaStatusCard />
        )}

        {/* API Keys */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-yellow-100 dark:bg-yellow-900/30 flex items-center justify-center">
                <Key className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />
              </div>
              <div>
                <CardTitle>API Keys</CardTitle>
                <CardDescription>
                  Securely stored in your system keychain
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {API_KEY_PROVIDERS.map((provider) => (
                <div
                  key={provider.id}
                  className={cn(
                    "flex items-center justify-between p-3 rounded-lg border transition-colors",
                    apiKeys[provider.id]
                      ? "border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/10"
                      : "border-gray-200 dark:border-gray-700"
                  )}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={cn(
                        "w-8 h-8 rounded-full flex items-center justify-center",
                        apiKeys[provider.id]
                          ? "bg-green-100 dark:bg-green-900/30"
                          : "bg-gray-100 dark:bg-gray-800"
                      )}
                    >
                      {apiKeys[provider.id] ? (
                        <Check className="w-4 h-4 text-green-600 dark:text-green-400" />
                      ) : (
                        <X className="w-4 h-4 text-gray-400" />
                      )}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">
                        {provider.name}
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {provider.description}
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => openApiKeyModal(provider.id)}
                    >
                      {apiKeys[provider.id] ? "Update" : "Add"}
                    </Button>
                    {apiKeys[provider.id] && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteApiKey(provider.id)}
                        className="text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
                      >
                        Delete
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* API Key Modal */}
      <Modal
        isOpen={showApiKeyModal}
        onClose={() => setShowApiKeyModal(false)}
        title={`${apiKeys[currentProvider || ""] ? "Update" : "Add"} API Key`}
        description={`Enter your ${currentProvider} API key. It will be stored securely in your system keychain.`}
        size="sm"
      >
        <Input
          type="password"
          label="API Key"
          value={apiKeyInput}
          onChange={(e) => setApiKeyInput(e.target.value)}
          placeholder="sk-..."
          autoFocus
        />
        <ModalFooter>
          <Button variant="secondary" onClick={() => setShowApiKeyModal(false)}>
            Cancel
          </Button>
          <Button onClick={handleSetApiKey} disabled={!apiKeyInput.trim()}>
            Save Key
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
