import { useState } from "react";
import {
  Database,
  Cpu,
  MessageSquare,
  Key,
  ArrowRight,
  ArrowLeft,
  Check,
  Sparkles,
  Shield,
  Zap,
} from "lucide-react";
import { Button, Card, Input, Select, type SelectOption } from "../components/ui";
import { cn } from "../lib/utils";
import { ipc } from "../lib/ipc";

interface OnboardingProps {
  onComplete: () => void;
}

const EMBEDDING_OPTIONS: SelectOption[] = [
  { value: "onnx_local", label: "ONNX Local (Recommended)" },
  { value: "openai", label: "OpenAI" },
  { value: "ollama", label: "Ollama" },
];

const LLM_OPTIONS: SelectOption[] = [
  { value: "ollama", label: "Ollama (Recommended)" },
  { value: "openai", label: "OpenAI" },
  { value: "anthropic", label: "Anthropic" },
];

export function Onboarding({ onComplete }: OnboardingProps) {
  const [step, setStep] = useState(0);
  const [embeddingProvider, setEmbeddingProvider] = useState("onnx_local");
  const [llmProvider, setLlmProvider] = useState("ollama");
  const [openaiKey, setOpenaiKey] = useState("");
  const [anthropicKey, setAnthropicKey] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const steps = [
    {
      id: "welcome",
      title: "Welcome to RAGKIT",
      icon: Sparkles,
      color: "primary",
    },
    {
      id: "embedding",
      title: "Choose Embedding Model",
      icon: Cpu,
      color: "blue",
    },
    {
      id: "llm",
      title: "Choose Language Model",
      icon: MessageSquare,
      color: "purple",
    },
    {
      id: "api-keys",
      title: "API Keys (Optional)",
      icon: Key,
      color: "yellow",
    },
    {
      id: "complete",
      title: "You're All Set!",
      icon: Check,
      color: "green",
    },
  ];

  const currentStep = steps[step];
  const needsApiKey =
    (embeddingProvider === "openai" || llmProvider === "openai") && !openaiKey;
  const needsAnthropicKey = llmProvider === "anthropic" && !anthropicKey;

  const handleNext = () => {
    if (step < steps.length - 1) {
      setStep(step + 1);
    }
  };

  const handleBack = () => {
    if (step > 0) {
      setStep(step - 1);
    }
  };

  const handleComplete = async () => {
    setIsSubmitting(true);
    try {
      // Save settings
      await ipc.updateSettings({
        embedding_provider: embeddingProvider,
        embedding_model:
          embeddingProvider === "onnx_local"
            ? "all-MiniLM-L6-v2"
            : embeddingProvider === "openai"
            ? "text-embedding-3-small"
            : "nomic-embed-text",
        llm_provider: llmProvider,
        llm_model:
          llmProvider === "ollama"
            ? "llama3.2:3b"
            : llmProvider === "openai"
            ? "gpt-4o-mini"
            : "claude-3-haiku-20240307",
        theme: "system",
      });

      // Save API keys if provided
      if (openaiKey) {
        await ipc.setApiKey("openai", openaiKey);
      }
      if (anthropicKey) {
        await ipc.setApiKey("anthropic", anthropicKey);
      }

      onComplete();
    } catch (error) {
      console.error("Failed to save onboarding settings:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const getColorClasses = (color: string) => {
    const colors: Record<string, { bg: string; icon: string }> = {
      primary: {
        bg: "bg-primary-100 dark:bg-primary-900/30",
        icon: "text-primary-600 dark:text-primary-400",
      },
      blue: {
        bg: "bg-blue-100 dark:bg-blue-900/30",
        icon: "text-blue-600 dark:text-blue-400",
      },
      purple: {
        bg: "bg-purple-100 dark:bg-purple-900/30",
        icon: "text-purple-600 dark:text-purple-400",
      },
      yellow: {
        bg: "bg-yellow-100 dark:bg-yellow-900/30",
        icon: "text-yellow-600 dark:text-yellow-400",
      },
      green: {
        bg: "bg-green-100 dark:bg-green-900/30",
        icon: "text-green-600 dark:text-green-400",
      },
    };
    return colors[color] || colors.primary;
  };

  const renderStepContent = () => {
    switch (currentStep.id) {
      case "welcome":
        return (
          <div className="text-center">
            <div className="grid grid-cols-3 gap-4 mt-8">
              <FeatureCard
                icon={Shield}
                title="Local-First"
                description="Your data stays on your device"
              />
              <FeatureCard
                icon={Zap}
                title="Fast"
                description="ONNX-powered embeddings"
              />
              <FeatureCard
                icon={Database}
                title="Flexible"
                description="Multiple providers supported"
              />
            </div>
            <p className="mt-8 text-gray-600 dark:text-gray-400">
              Let's set up RAGKIT in a few quick steps.
            </p>
          </div>
        );

      case "embedding":
        return (
          <div className="space-y-6">
            <p className="text-gray-600 dark:text-gray-400">
              Embeddings convert your documents into vectors for semantic search.
              We recommend ONNX Local for privacy and offline use.
            </p>
            <Select
              label="Embedding Provider"
              options={EMBEDDING_OPTIONS}
              value={embeddingProvider}
              onChange={(e) => setEmbeddingProvider(e.target.value)}
            />
            {embeddingProvider === "onnx_local" && (
              <div className="flex items-start gap-3 p-4 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
                <Shield className="w-5 h-5 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-green-800 dark:text-green-200">
                    100% Offline
                  </p>
                  <p className="text-sm text-green-700 dark:text-green-300">
                    No API key needed. Models run entirely on your device.
                  </p>
                </div>
              </div>
            )}
          </div>
        );

      case "llm":
        return (
          <div className="space-y-6">
            <p className="text-gray-600 dark:text-gray-400">
              The language model generates answers from your documents.
              Ollama runs locally, while OpenAI and Anthropic offer cloud models.
            </p>
            <Select
              label="Language Model Provider"
              options={LLM_OPTIONS}
              value={llmProvider}
              onChange={(e) => setLlmProvider(e.target.value)}
            />
            {llmProvider === "ollama" && (
              <div className="flex items-start gap-3 p-4 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
                <Shield className="w-5 h-5 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-green-800 dark:text-green-200">
                    Local LLM
                  </p>
                  <p className="text-sm text-green-700 dark:text-green-300">
                    Make sure Ollama is installed and running on your system.
                  </p>
                </div>
              </div>
            )}
          </div>
        );

      case "api-keys":
        return (
          <div className="space-y-6">
            <p className="text-gray-600 dark:text-gray-400">
              {needsApiKey || needsAnthropicKey
                ? "Enter the API keys for your selected providers."
                : "You've selected local providers. API keys are optional but can be added later in Settings."}
            </p>

            {(embeddingProvider === "openai" || llmProvider === "openai") && (
              <Input
                type="password"
                label="OpenAI API Key"
                value={openaiKey}
                onChange={(e) => setOpenaiKey(e.target.value)}
                placeholder="sk-..."
                hint="Required for OpenAI models"
              />
            )}

            {llmProvider === "anthropic" && (
              <Input
                type="password"
                label="Anthropic API Key"
                value={anthropicKey}
                onChange={(e) => setAnthropicKey(e.target.value)}
                placeholder="sk-ant-..."
                hint="Required for Claude models"
              />
            )}

            {!needsApiKey && !needsAnthropicKey && (
              <div className="flex items-start gap-3 p-4 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
                <Check className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-blue-800 dark:text-blue-200">
                    No API keys needed!
                  </p>
                  <p className="text-sm text-blue-700 dark:text-blue-300">
                    You can add them later in Settings if you want to use cloud providers.
                  </p>
                </div>
              </div>
            )}
          </div>
        );

      case "complete":
        return (
          <div className="text-center space-y-6">
            <div className="w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br from-green-100 to-green-200 dark:from-green-900/30 dark:to-green-800/30 flex items-center justify-center">
              <Check className="w-10 h-10 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
                Setup Complete!
              </h3>
              <p className="mt-2 text-gray-600 dark:text-gray-400">
                You're ready to create your first knowledge base and start querying your documents.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-4 pt-4">
              <SummaryItem
                label="Embeddings"
                value={EMBEDDING_OPTIONS.find((o) => o.value === embeddingProvider)?.label || ""}
              />
              <SummaryItem
                label="LLM"
                value={LLM_OPTIONS.find((o) => o.value === llmProvider)?.label || ""}
              />
            </div>
          </div>
        );
    }
  };

  const colorClasses = getColorClasses(currentStep.color);
  const Icon = currentStep.icon;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
      <Card className="w-full max-w-lg">
        {/* Progress */}
        <div className="flex gap-1 mb-6">
          {steps.map((s, i) => (
            <div
              key={s.id}
              className={cn(
                "h-1 flex-1 rounded-full transition-colors",
                i <= step
                  ? "bg-primary-600 dark:bg-primary-500"
                  : "bg-gray-200 dark:bg-gray-700"
              )}
            />
          ))}
        </div>

        {/* Header */}
        <div className="flex items-center gap-4 mb-6">
          <div
            className={cn(
              "w-12 h-12 rounded-xl flex items-center justify-center",
              colorClasses.bg
            )}
          >
            <Icon className={cn("w-6 h-6", colorClasses.icon)} />
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Step {step + 1} of {steps.length}
            </p>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              {currentStep.title}
            </h2>
          </div>
        </div>

        {/* Content */}
        <div className="min-h-[200px]">{renderStepContent()}</div>

        {/* Navigation */}
        <div className="flex items-center justify-between mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
          {step > 0 ? (
            <Button variant="ghost" onClick={handleBack}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
          ) : (
            <div />
          )}

          {step < steps.length - 1 ? (
            <Button onClick={handleNext}>
              Next
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          ) : (
            <Button onClick={handleComplete} isLoading={isSubmitting}>
              Get Started
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          )}
        </div>
      </Card>
    </div>
  );
}

// Feature card for welcome screen
function FeatureCard({
  icon: Icon,
  title,
  description,
}: {
  icon: typeof Shield;
  title: string;
  description: string;
}) {
  return (
    <div className="p-4 rounded-xl bg-gray-100 dark:bg-gray-800 text-center">
      <div className="w-10 h-10 mx-auto rounded-lg bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center mb-3">
        <Icon className="w-5 h-5 text-primary-600 dark:text-primary-400" />
      </div>
      <h3 className="font-medium text-gray-900 dark:text-white">{title}</h3>
      <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{description}</p>
    </div>
  );
}

// Summary item for completion screen
function SummaryItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-3 rounded-lg bg-gray-100 dark:bg-gray-800 text-left">
      <p className="text-xs text-gray-500 dark:text-gray-400">{label}</p>
      <p className="font-medium text-gray-900 dark:text-white">{value}</p>
    </div>
  );
}
