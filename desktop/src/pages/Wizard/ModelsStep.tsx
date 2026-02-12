import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Cpu, Key, Monitor, Server } from "lucide-react";
import {
  Button,
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
  Input,
  Select,
  useToast,
} from "../../components/ui";
import { ipc, EnvironmentDetection, WizardProfileResponse } from "../../lib/ipc";

export interface ModelsSelection {
  embeddingProvider: string;
  embeddingModel: string;
  llmProvider: string;
  llmModel: string;
  openaiKey?: string;
  anthropicKey?: string;
}

interface ModelsStepProps {
  profile: WizardProfileResponse | null;
  onNext: (models: ModelsSelection) => void;
  onBack: () => void;
  initialModels?: ModelsSelection | null;
}

export function ModelsStep({ profile, onNext, onBack, initialModels }: ModelsStepProps) {
  const { t } = useTranslation();
  const toast = useToast();
  const [environment, setEnvironment] = useState<EnvironmentDetection | null>(null);
  const [loadingEnv, setLoadingEnv] = useState(true);
  const [selection, setSelection] = useState<ModelsSelection>(
    initialModels || {
      embeddingProvider: "onnx_local",
      embeddingModel: "all-MiniLM-L6-v2",
      llmProvider: "ollama",
      llmModel: "llama3.2:3b",
      openaiKey: "",
      anthropicKey: "",
    }
  );

  const embeddingProviders = [
    { value: "onnx_local", label: t("wizard.models.providers.onnxLocal") },
    { value: "openai", label: t("wizard.models.providers.openai") },
    { value: "ollama", label: t("wizard.models.providers.ollama") },
  ];

  const embeddingModels: Record<string, { value: string; label: string }[]> = {
    onnx_local: [{ value: "all-MiniLM-L6-v2", label: "all-MiniLM-L6-v2" }],
    openai: [{ value: "text-embedding-3-small", label: "text-embedding-3-small" }],
    ollama: [{ value: "nomic-embed-text", label: "nomic-embed-text" }],
  };

  const llmProviders = [
    { value: "ollama", label: t("wizard.models.providers.ollamaRecommended") },
    { value: "openai", label: t("wizard.models.providers.openai") },
    { value: "anthropic", label: t("wizard.models.providers.anthropic") },
  ];

  const llmModels: Record<string, { value: string; label: string }[]> = {
    ollama: [
      { value: "llama3.2:3b", label: "Llama 3.2 3B" },
      { value: "llama3.1:8b", label: "Llama 3.1 8B" },
    ],
    openai: [
      { value: "gpt-4o-mini", label: "GPT-4o Mini" },
      { value: "gpt-4o", label: "GPT-4o" },
    ],
    anthropic: [
      { value: "claude-3-haiku-20240307", label: "Claude 3 Haiku" },
      { value: "claude-3-5-sonnet-20241022", label: "Claude 3.5 Sonnet" },
    ],
  };

  useEffect(() => {
    let mounted = true;
    const loadEnvironment = async () => {
      try {
        const env = await ipc.detectEnvironment();
        if (mounted) {
          setEnvironment(env);
        }
      } catch (error) {
        console.error("Failed to detect environment:", error);
        toast.error(
          t("wizard.models.environmentErrorTitle"),
          t("wizard.models.environmentErrorMessage")
        );
      } finally {
        if (mounted) {
          setLoadingEnv(false);
        }
      }
    };
    loadEnvironment();

    return () => {
      mounted = false;
    };
  }, [toast, t]);

  const embeddingModelOptions = embeddingModels[selection.embeddingProvider] || [];
  const llmModelOptions = llmModels[selection.llmProvider] || [];

  const handleNext = () => {
    onNext(selection);
  };

  const showOpenAIKey =
    selection.embeddingProvider === "openai" || selection.llmProvider === "openai";
  const showAnthropicKey = selection.llmProvider === "anthropic";

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{t("wizard.models.title")}</CardTitle>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {t("wizard.models.subtitle")}
          </p>
        </CardHeader>
        <CardContent className="space-y-6">
          {profile && (
            <div className="p-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/60">
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                {t("wizard.models.recommendedProfile")}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">{profile.profile_name}</p>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                {profile.description}
              </p>
            </div>
          )}

          <div className="grid gap-4 sm:grid-cols-2">
            <Select
              label={t("wizard.models.embeddingProviderLabel")}
              options={embeddingProviders}
              value={selection.embeddingProvider}
              onChange={(e) => {
                const provider = e.target.value;
                const nextModel = embeddingModels[provider]?.[0]?.value || "";
                setSelection((prev) => ({
                  ...prev,
                  embeddingProvider: provider,
                  embeddingModel: nextModel,
                }));
              }}
            />
            <Select
              label={t("wizard.models.embeddingModelLabel")}
              options={embeddingModelOptions}
              value={selection.embeddingModel}
              onChange={(e) =>
                setSelection((prev) => ({ ...prev, embeddingModel: e.target.value }))
              }
            />
            <Select
              label={t("wizard.models.llmProviderLabel")}
              options={llmProviders}
              value={selection.llmProvider}
              onChange={(e) => {
                const provider = e.target.value;
                const nextModel = llmModels[provider]?.[0]?.value || "";
                setSelection((prev) => ({
                  ...prev,
                  llmProvider: provider,
                  llmModel: nextModel,
                }));
              }}
            />
            <Select
              label={t("wizard.models.llmModelLabel")}
              options={llmModelOptions}
              value={selection.llmModel}
              onChange={(e) =>
                setSelection((prev) => ({ ...prev, llmModel: e.target.value }))
              }
            />
          </div>

          {(showOpenAIKey || showAnthropicKey) && (
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                <Key className="w-4 h-4" />
                {t("wizard.models.apiKeysTitle")}
              </div>
              {showOpenAIKey && (
                <Input
                  type="password"
                  label={t("wizard.models.openaiKeyLabel")}
                  value={selection.openaiKey || ""}
                  onChange={(e) =>
                    setSelection((prev) => ({ ...prev, openaiKey: e.target.value }))
                  }
                  placeholder="sk-..."
                />
              )}
              {showAnthropicKey && (
                <Input
                  type="password"
                  label={t("wizard.models.anthropicKeyLabel")}
                  value={selection.anthropicKey || ""}
                  onChange={(e) =>
                    setSelection((prev) => ({ ...prev, anthropicKey: e.target.value }))
                  }
                  placeholder="sk-ant-..."
                />
              )}
            </div>
          )}
        </CardContent>
        <CardFooter className="justify-between">
          <Button variant="ghost" onClick={onBack}>
            {t("common.actions.back")}
          </Button>
          <Button onClick={handleNext}>{t("common.actions.continue")}</Button>
        </CardFooter>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t("wizard.models.environmentTitle")}</CardTitle>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {t("wizard.models.environmentSubtitle")}
          </p>
        </CardHeader>
        <CardContent>
          {loadingEnv ? (
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {t("wizard.models.detectingEnvironment")}
            </p>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              <EnvCard
                icon={Monitor}
                title={t("wizard.models.environment.gpu")}
                value={
                  environment?.gpu.detected
                    ? t("wizard.models.environment.detected")
                    : t("wizard.models.environment.notDetected")
                }
                detail={
                  environment?.gpu.detected
                    ? `${environment?.gpu.name || "GPU"} (${environment?.gpu.vram_free_gb || "?"} GB)`
                    : t("wizard.models.environment.cpuOnly")
                }
              />
              <EnvCard
                icon={Server}
                title={t("wizard.models.environment.ollama")}
                value={
                  environment?.ollama.running
                    ? t("wizard.models.environment.running")
                    : environment?.ollama.installed
                    ? t("wizard.models.environment.installed")
                    : t("wizard.models.environment.notInstalled")
                }
                detail={
                  environment?.ollama.installed
                    ? t("wizard.models.environment.version", {
                        version: environment?.ollama.version || t("wizard.models.environment.unknown"),
                      })
                    : t("wizard.models.environment.localUnavailable")
                }
              />
            </div>
          )}
          {environment?.ollama.installed && !environment?.ollama.running && (
            <p className="mt-3 text-sm text-amber-600 dark:text-amber-400">
              {t("wizard.models.environment.ollamaNotRunning")}
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function EnvCard({
  icon: Icon,
  title,
  value,
  detail,
}: {
  icon: typeof Cpu;
  title: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="flex items-start gap-3 p-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/60">
      <div className="w-10 h-10 rounded-lg bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
        <Icon className="w-5 h-5 text-primary-600 dark:text-primary-400" />
      </div>
      <div>
        <p className="text-sm font-medium text-gray-900 dark:text-white">{title}</p>
        <p className="text-sm text-gray-700 dark:text-gray-300">{value}</p>
        <p className="text-xs text-gray-500 dark:text-gray-400">{detail}</p>
      </div>
    </div>
  );
}
