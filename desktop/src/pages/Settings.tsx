import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
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
  Textarea,
  useToast,
  useConfirm,
  type SelectOption,
} from "../components/ui";
import { cn } from "../lib/utils";

type ExpertiseLevel = "beginner" | "intermediate" | "expert";

type SettingsTab = "general" | "advanced" | "json";

const EXPERTISE_STORAGE_KEY = "ragkit.settings.expertise";

const EMBEDDING_PROVIDER_OPTIONS = [
  { value: "onnx_local", labelKey: "settings.embedding.providers.onnx_local" },
  { value: "openai", labelKey: "settings.embedding.providers.openai" },
  { value: "cohere", labelKey: "settings.embedding.providers.cohere" },
  { value: "ollama", labelKey: "settings.embedding.providers.ollama" },
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

const LLM_PROVIDER_OPTIONS = [
  { value: "ollama", labelKey: "settings.llm.providers.ollama" },
  { value: "openai", labelKey: "settings.llm.providers.openai" },
  { value: "anthropic", labelKey: "settings.llm.providers.anthropic" },
  { value: "deepseek", labelKey: "settings.llm.providers.deepseek" },
  { value: "groq", labelKey: "settings.llm.providers.groq" },
  { value: "mistral", labelKey: "settings.llm.providers.mistral" },
  { value: "gemini", labelKey: "settings.llm.providers.gemini" },
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
  { id: "openai", name: "OpenAI", descriptionKey: "settings.apiKeys.providers.openai" },
  {
    id: "anthropic",
    name: "Anthropic",
    descriptionKey: "settings.apiKeys.providers.anthropic",
  },
  { id: "deepseek", name: "DeepSeek", descriptionKey: "settings.apiKeys.providers.deepseek" },
  { id: "groq", name: "Groq", descriptionKey: "settings.apiKeys.providers.groq" },
  { id: "mistral", name: "Mistral", descriptionKey: "settings.apiKeys.providers.mistral" },
  { id: "gemini", name: "Gemini", descriptionKey: "settings.apiKeys.providers.gemini" },
  { id: "cohere", name: "Cohere", descriptionKey: "settings.apiKeys.providers.cohere" },
];

const CHUNKING_STRATEGIES = [
  { value: "fixed", labelKey: "settings.chunking.strategies.fixed" },
  { value: "semantic", labelKey: "settings.chunking.strategies.semantic" },
];

const RETRIEVAL_ARCHITECTURES = [
  { value: "semantic", labelKey: "settings.retrieval.architectures.semantic" },
  { value: "lexical", labelKey: "settings.retrieval.architectures.lexical" },
  { value: "hybrid", labelKey: "settings.retrieval.architectures.hybrid" },
  { value: "hybrid_rerank", labelKey: "settings.retrieval.architectures.hybrid_rerank" },
];

const RERANK_PROVIDERS = [
  { value: "none", labelKey: "settings.retrieval.rerankProviders.none" },
  { value: "cohere", labelKey: "settings.retrieval.rerankProviders.cohere" },
];

export function Settings() {
  const { t, i18n } = useTranslation();
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
  const [expertiseLevel, setExpertiseLevel] = useState<ExpertiseLevel>(() => {
    if (typeof window === "undefined") return "beginner";
    try {
      const stored = window.localStorage.getItem(EXPERTISE_STORAGE_KEY) as ExpertiseLevel | null;
      if (stored === "beginner" || stored === "intermediate" || stored === "expert") {
        return stored;
      }
    } catch {
      // ignore
    }
    return "beginner";
  });
  const [activeTab, setActiveTab] = useState<SettingsTab>("general");
  const [jsonDraft, setJsonDraft] = useState("");
  const [jsonError, setJsonError] = useState("");

  const tabs = useMemo<SettingsTab[]>(() => {
    if (expertiseLevel === "beginner") return ["general"];
    if (expertiseLevel === "intermediate") return ["general", "advanced"];
    return ["general", "advanced", "json"];
  }, [expertiseLevel]);

  useEffect(() => {
    if (!tabs.includes(activeTab)) {
      setActiveTab(tabs[0]);
    }
  }, [tabs, activeTab]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      window.localStorage.setItem(EXPERTISE_STORAGE_KEY, expertiseLevel);
    } catch {
      // ignore storage errors
    }
  }, [expertiseLevel]);

  useEffect(() => {
    if (!settings) return;
    if (activeTab === "json") {
      setJsonDraft(JSON.stringify(settings, null, 2));
      setJsonError("");
    }
  }, [activeTab, settings]);

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
      toast.error(t("settings.toasts.loadFailed"));
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!settings) return;

    try {
      setIsSaving(true);
      await ipc.updateSettings(settings);
      toast.success(t("settings.toasts.saveSuccessTitle"), t("settings.toasts.saveSuccessMessage"));
    } catch (error) {
      console.error("Failed to save settings:", error);
      toast.error(t("settings.toasts.saveFailed"));
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
      toast.success(
        t("settings.toasts.apiKeySavedTitle"),
        t("settings.toasts.apiKeySavedMessage", { provider: currentProvider })
      );
    } catch (error) {
      console.error("Failed to set API key:", error);
      toast.error(t("settings.toasts.apiKeySaveFailed"));
    }
  };

  const handleDeleteApiKey = async (provider: string) => {
    const confirmed = await confirm({
      title: t("settings.apiKeys.deleteTitle"),
      message: t("settings.apiKeys.deleteMessage", { provider }),
      confirmLabel: t("common.actions.delete"),
      cancelLabel: t("common.actions.cancel"),
      variant: "warning",
    });

    if (!confirmed) return;

    try {
      await ipc.deleteApiKey(provider);
      setApiKeys((prev) => ({ ...prev, [provider]: false }));
      toast.info(
        t("settings.toasts.apiKeyDeletedTitle"),
        t("settings.toasts.apiKeyDeletedMessage", { provider })
      );
    } catch (error) {
      console.error("Failed to delete API key:", error);
      toast.error(t("settings.toasts.apiKeyDeleteFailed"));
    }
  };

  const handleApplyJson = () => {
    if (!settings) return;

    try {
      const parsed = JSON.parse(jsonDraft);
      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
        setJsonError(t("settings.json.invalidMessage"));
        toast.error(t("settings.json.invalidTitle"), t("settings.json.invalidMessage"));
        return;
      }
      const nextSettings = { ...settings, ...parsed } as SettingsType;
      setSettings(nextSettings);
      setJsonError("");
      toast.success(t("settings.json.applySuccessTitle"), t("settings.json.applySuccessMessage"));
    } catch (err) {
      setJsonError(t("settings.json.invalidMessage"));
      toast.error(t("settings.json.invalidTitle"), t("settings.json.invalidMessage"));
    }
  };

  if (isLoading || !settings) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <Loader2 className="w-10 h-10 text-primary-600 animate-spin" />
        <p className="mt-4 text-gray-500 dark:text-gray-400">{t("settings.loading")}</p>
      </div>
    );
  }

  const embeddingProviders = EMBEDDING_PROVIDER_OPTIONS.map((option) => ({
    value: option.value,
    label: t(option.labelKey),
  }));
  const llmProviders = LLM_PROVIDER_OPTIONS.map((option) => ({
    value: option.value,
    label: t(option.labelKey),
  }));
  const chunkingStrategies = CHUNKING_STRATEGIES.map((option) => ({
    value: option.value,
    label: t(option.labelKey),
  }));
  const retrievalArchitectures = RETRIEVAL_ARCHITECTURES.map((option) => ({
    value: option.value,
    label: t(option.labelKey),
  }));
  const rerankProviders = RERANK_PROVIDERS.map((option) => ({
    value: option.value,
    label: t(option.labelKey),
  }));

  const embeddingModels = EMBEDDING_MODELS[settings.embedding_provider] || [];
  const llmModels = LLM_MODELS[settings.llm_provider] || [];
  const languageOptions = [
    { value: "fr", label: t("language.fr") },
    { value: "en", label: t("language.en") },
  ];
  const expertiseOptions = [
    { value: "beginner", label: t("settings.expertise.beginner") },
    { value: "intermediate", label: t("settings.expertise.intermediate") },
    { value: "expert", label: t("settings.expertise.expert") },
  ];

  return (
    <div className="h-full overflow-auto">
      {/* Header */}
      <header className="sticky top-0 z-10 flex flex-col gap-4 px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
            <Settings2 className="w-5 h-5 text-primary-600 dark:text-primary-400" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
              {t("settings.title")}
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {t("settings.subtitle")}
            </p>
          </div>
        </div>
        <div className="flex flex-wrap items-end gap-3">
          <div className="w-44">
            <Select
              label={t("settings.language.label")}
              options={languageOptions}
              value={i18n.language}
              onChange={(e) => i18n.changeLanguage(e.target.value)}
            />
          </div>
          <div className="w-48">
            <Select
              label={t("settings.expertise.label")}
              options={expertiseOptions}
              value={expertiseLevel}
              onChange={(e) => setExpertiseLevel(e.target.value as ExpertiseLevel)}
            />
          </div>
          <Button onClick={handleSave} isLoading={isSaving}>
            <Save className="w-4 h-4 mr-2" />
            {t("common.actions.save")}
          </Button>
        </div>
      </header>

      {/* Tabs */}
      <div className="px-6 pt-4">
        <div className="flex flex-wrap gap-2">
          {tabs.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={cn(
                "px-4 py-2 rounded-lg text-sm font-medium transition-colors",
                activeTab === tab
                  ? "bg-primary-600 text-white"
                  : "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-200"
              )}
            >
              {t(`settings.tabs.${tab}`)}
            </button>
          ))}
        </div>
      </div>

      {/* Settings Sections */}
      <div className="p-6 max-w-3xl space-y-6">
        {activeTab === "general" && (
          <>
            {/* Embedding Settings */}
            <Card>
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                    <Cpu className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <CardTitle>{t("settings.embedding.title")}</CardTitle>
                    <CardDescription>{t("settings.embedding.description")}</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 sm:grid-cols-2">
                  <Select
                    label={t("settings.labels.provider")}
                    options={embeddingProviders}
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
                      label={t("settings.labels.customModel")}
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
                      label={t("settings.labels.model")}
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
                    {embeddingUseCustomModel
                      ? t("settings.actions.usePreset")
                      : t("settings.actions.useCustom")}
                  </Button>
                </div>
                {settings.embedding_provider === "onnx_local" && (
                  <p className="mt-3 text-sm text-green-600 dark:text-green-400 flex items-center gap-1">
                    <ShieldCheck className="w-4 h-4" />
                    {t("settings.notices.localNoKey")}
                  </p>
                )}
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
                    <CardTitle>{t("settings.llm.title")}</CardTitle>
                    <CardDescription>{t("settings.llm.description")}</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 sm:grid-cols-2">
                  <Select
                    label={t("settings.labels.provider")}
                    options={llmProviders}
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
                      label={t("settings.labels.customModel")}
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
                      label={t("settings.labels.model")}
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
                    {llmUseCustomModel
                      ? t("settings.actions.usePreset")
                      : t("settings.actions.useCustom")}
                  </Button>
                </div>
                {settings.llm_provider === "ollama" && (
                  <p className="mt-3 text-sm text-green-600 dark:text-green-400 flex items-center gap-1">
                    <ShieldCheck className="w-4 h-4" />
                    {t("settings.notices.localNoKey")}
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
                    <CardTitle>{t("settings.apiKeys.title")}</CardTitle>
                    <CardDescription>{t("settings.apiKeys.description")}</CardDescription>
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
                            {t(provider.descriptionKey)}
                          </p>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => openApiKeyModal(provider.id)}
                        >
                          {apiKeys[provider.id]
                            ? t("common.actions.update")
                            : t("common.actions.add")}
                        </Button>
                        {apiKeys[provider.id] && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteApiKey(provider.id)}
                            className="text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
                          >
                            {t("common.actions.delete")}
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </>
        )}

        {activeTab === "advanced" && (
          <>
            {/* Chunking Settings */}
            <Card>
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center">
                    <SlidersHorizontal className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
                  </div>
                  <div>
                    <CardTitle>{t("settings.chunking.title")}</CardTitle>
                    <CardDescription>{t("settings.chunking.description")}</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 sm:grid-cols-2">
                  <Select
                    label={t("settings.labels.strategy")}
                    options={chunkingStrategies}
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
                    label={t("settings.labels.chunkSize")}
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
                    hint={t("settings.hints.chunkSize")}
                  />
                  <Input
                    type="number"
                    label={t("settings.labels.chunkOverlap")}
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
                    hint={t("settings.hints.chunkOverlap")}
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
                    <CardTitle>{t("settings.retrieval.title")}</CardTitle>
                    <CardDescription>{t("settings.retrieval.description")}</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 sm:grid-cols-2">
                  <Select
                    label={t("settings.labels.architecture")}
                    options={retrievalArchitectures}
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
                    label={t("settings.labels.topK")}
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
                    hint={t("settings.hints.topK")}
                  />
                  <Input
                    type="number"
                    label={t("settings.labels.semanticWeight")}
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
                    label={t("settings.labels.lexicalWeight")}
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
                    label={t("settings.labels.rerankWeight")}
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
                    label={t("settings.labels.maxChunks")}
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
                    hint={t("settings.hints.maxChunks")}
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
                    {t("settings.labels.enableReranking")}
                  </label>
                  <div className="sm:w-56">
                    <Select
                      label={t("settings.labels.rerankProvider")}
                      options={rerankProviders}
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
          </>
        )}

        {activeTab === "json" && (
          <Card>
            <CardHeader>
              <CardTitle>{t("settings.json.title")}</CardTitle>
              <CardDescription>{t("settings.json.description")}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                value={jsonDraft}
                onChange={(e) => setJsonDraft(e.target.value)}
                placeholder={t("settings.json.placeholder")}
                hint={jsonError ? undefined : t("settings.json.hint")}
                error={jsonError || undefined}
              />
              <div className="flex justify-end">
                <Button variant="secondary" onClick={handleApplyJson}>
                  {t("settings.json.apply")}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* API Key Modal */}
      <Modal
        isOpen={showApiKeyModal}
        onClose={() => setShowApiKeyModal(false)}
        title={
          apiKeys[currentProvider || ""]
            ? t("settings.apiKeys.modalTitleUpdate")
            : t("settings.apiKeys.modalTitleAdd")
        }
        description={t("settings.apiKeys.modalDescription", {
          provider: currentProvider || "",
        })}
        size="sm"
      >
        <Input
          type="password"
          label={t("settings.labels.apiKey")}
          value={apiKeyInput}
          onChange={(e) => setApiKeyInput(e.target.value)}
          placeholder="sk-..."
          autoFocus
        />
        <ModalFooter>
          <Button variant="secondary" onClick={() => setShowApiKeyModal(false)}>
            {t("common.actions.cancel")}
          </Button>
          <Button onClick={handleSetApiKey} disabled={!apiKeyInput.trim()}>
            {t("settings.apiKeys.saveKey")}
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
}
