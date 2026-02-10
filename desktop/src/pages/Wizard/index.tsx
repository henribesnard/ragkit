import { useMemo, useState } from "react";
import { useToast } from "../../components/ui";
import { ipc, Settings, WizardProfileResponse } from "../../lib/ipc";
import { FolderStep, type FolderSelection } from "./FolderStep";
import { ModelsStep, type ModelsSelection } from "./ModelsStep";
import { ProfileStep, type ProfileResult } from "./ProfileStep";
import { SummaryStep } from "./SummaryStep";
import { WelcomeStep } from "./WelcomeStep";

type WizardStep = "welcome" | "profile" | "models" | "folder" | "summary";

interface WizardProps {
  onComplete?: () => void;
}

export function Wizard({ onComplete }: WizardProps) {
  const toast = useToast();
  const [currentStep, setCurrentStep] = useState<WizardStep>("welcome");
  const [wizardData, setWizardData] = useState<{
    profile: ProfileResult | null;
    models: ModelsSelection | null;
    folder: FolderSelection | null;
  }>({
    profile: null,
    models: null,
    folder: null,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const steps: WizardStep[] = ["welcome", "profile", "models", "folder", "summary"];
  const currentStepIndex = steps.indexOf(currentStep);
  const progress = ((currentStepIndex + 1) / steps.length) * 100;

  const profileSummary = useMemo(() => {
    return wizardData.profile?.analysis || null;
  }, [wizardData.profile]);

  const handleConfirm = async () => {
    setIsSubmitting(true);
    try {
      const currentSettings = await ipc.getSettings();
      const nextSettings = buildSettingsFromWizard(
        currentSettings,
        wizardData.profile?.analysis || null,
        wizardData.models
      );
      await ipc.updateSettings(nextSettings);

      if (wizardData.models?.openaiKey) {
        await ipc.setApiKey("openai", wizardData.models.openaiKey);
      }
      if (wizardData.models?.anthropicKey) {
        await ipc.setApiKey("anthropic", wizardData.models.anthropicKey);
      }

      onComplete?.();
    } catch (error) {
      console.error("Failed to finalize wizard:", error);
      toast.error("Setup failed", "Please review your selections and try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* Progress bar */}
      <div className="h-2 bg-gray-200 dark:bg-gray-700">
        <div
          className="h-full bg-primary-600 transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Step indicator */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex flex-wrap items-center justify-between max-w-4xl mx-auto gap-3">
          {["Welcome", "Profile", "Models", "Folder", "Summary"].map((label, idx) => (
            <div
              key={label}
              className={`flex items-center gap-2 text-sm ${
                idx <= currentStepIndex ? "text-primary-600" : "text-gray-400"
              }`}
            >
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold ${
                  idx <= currentStepIndex
                    ? "bg-primary-600 text-white"
                    : "bg-gray-200 text-gray-500"
                }`}
              >
                {idx + 1}
              </div>
              <span className="hidden sm:inline">{label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Step content */}
      <div className="flex-1 overflow-auto">
        {currentStep === "welcome" && (
          <WelcomeStep onNext={() => setCurrentStep("profile")} />
        )}
        {currentStep === "profile" && (
          <ProfileStep
            initialAnswers={wizardData.profile?.answers}
            onNext={(profile) => {
              setWizardData((prev) => ({ ...prev, profile }));
              setCurrentStep("models");
            }}
            onBack={() => setCurrentStep("welcome")}
          />
        )}
        {currentStep === "models" && (
          <ModelsStep
            profile={profileSummary}
            initialModels={wizardData.models}
            onNext={(models) => {
              setWizardData((prev) => ({ ...prev, models }));
              setCurrentStep("folder");
            }}
            onBack={() => setCurrentStep("profile")}
          />
        )}
        {currentStep === "folder" && (
          <FolderStep
            initialFolder={wizardData.folder}
            onNext={(folder) => {
              setWizardData((prev) => ({ ...prev, folder }));
              setCurrentStep("summary");
            }}
            onBack={() => setCurrentStep("models")}
          />
        )}
        {currentStep === "summary" && (
          <SummaryStep
            wizardData={wizardData}
            onConfirm={handleConfirm}
            onBack={() => setCurrentStep("folder")}
            isSubmitting={isSubmitting}
          />
        )}
      </div>
    </div>
  );
}

function buildSettingsFromWizard(
  current: Settings,
  profile: WizardProfileResponse | null,
  models: ModelsSelection | null
): Settings {
  const next = { ...current };

  if (models) {
    next.embedding_provider = models.embeddingProvider;
    next.embedding_model = models.embeddingModel;
    next.llm_provider = models.llmProvider;
    next.llm_model = models.llmModel;
  }

  const profileConfig = profile?.full_config || {};
  const chunking = (profileConfig as Record<string, any>).chunking || {};
  const retrieval = (profileConfig as Record<string, any>).retrieval || {};
  const reranking = (profileConfig as Record<string, any>).reranking || {};

  const chunkStrategy = chunking.strategy === "semantic" ? "semantic" : "fixed";
  const chunkSize =
    typeof chunking.chunk_size === "number"
      ? chunking.chunk_size
      : typeof chunking.child_chunk_size === "number"
      ? chunking.child_chunk_size
      : next.embedding_chunk_size;
  const chunkOverlap =
    typeof chunking.chunk_overlap === "number"
      ? chunking.chunk_overlap
      : next.embedding_chunk_overlap;

  next.embedding_chunk_strategy = chunkStrategy;
  next.embedding_chunk_size = chunkSize;
  next.embedding_chunk_overlap = chunkOverlap;

  const architecture = retrieval.architecture;
  if (
    architecture === "semantic" ||
    architecture === "lexical" ||
    architecture === "hybrid" ||
    architecture === "hybrid_rerank"
  ) {
    next.retrieval_architecture = architecture;
  }

  if (typeof retrieval.top_k === "number") {
    next.retrieval_top_k = retrieval.top_k;
  }

  if (next.retrieval_architecture === "semantic") {
    next.retrieval_semantic_weight = 1.0;
    next.retrieval_lexical_weight = 0.0;
  } else if (next.retrieval_architecture === "lexical") {
    next.retrieval_semantic_weight = 0.0;
    next.retrieval_lexical_weight = 1.0;
  } else if (typeof retrieval.alpha === "number") {
    next.retrieval_semantic_weight = Math.min(1, Math.max(0, retrieval.alpha));
    next.retrieval_lexical_weight = Math.min(1, Math.max(0, 1 - retrieval.alpha));
  }

  next.retrieval_rerank_enabled = Boolean(reranking.enabled);
  if (next.retrieval_architecture === "hybrid_rerank") {
    next.retrieval_rerank_enabled = true;
  }

  return next;
}
