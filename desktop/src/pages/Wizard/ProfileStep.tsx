import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Button, Card, CardContent, CardFooter, CardHeader, CardTitle, Select, useToast } from "../../components/ui";
import { ipc, WizardAnswers, WizardProfileResponse } from "../../lib/ipc";

interface ProfileStepProps {
  onNext: (payload: ProfileResult) => void;
  onBack: () => void;
  initialAnswers?: WizardAnswers;
}

export interface ProfileResult {
  answers: WizardAnswers;
  analysis: WizardProfileResponse;
}

export function ProfileStep({ onNext, onBack, initialAnswers }: ProfileStepProps) {
  const { t } = useTranslation();
  const toast = useToast();
  const [answers, setAnswers] = useState<WizardAnswers>(
    initialAnswers || {
      kb_type: "technical_documentation",
      has_tables_diagrams: false,
      needs_multi_document: false,
      large_documents: false,
      needs_precision: false,
      frequent_updates: false,
      cite_page_numbers: false,
    }
  );
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const kbTypeOptions = [
    { value: "technical_documentation", label: t("wizard.profile.kbTypes.technical") },
    { value: "faq_support", label: t("wizard.profile.kbTypes.faq") },
    { value: "legal_regulatory", label: t("wizard.profile.kbTypes.legal") },
    { value: "reports_analysis", label: t("wizard.profile.kbTypes.reports") },
    { value: "general_knowledge", label: t("wizard.profile.kbTypes.general") },
  ];

  const handleToggle = (key: keyof WizardAnswers) => {
    setAnswers((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleNext = async () => {
    setIsAnalyzing(true);
    try {
      const analysis = await ipc.analyzeWizardProfile(answers);
      onNext({ answers, analysis });
    } catch (error) {
      console.error("Failed to analyze profile:", error);
      toast.error(
        t("wizard.profile.analysisFailedTitle"),
        t("wizard.profile.analysisFailedMessage")
      );
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <Card>
        <CardHeader>
          <CardTitle>{t("wizard.profile.title")}</CardTitle>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {t("wizard.profile.subtitle")}
          </p>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            <Select
              label={t("wizard.profile.kbTypeLabel")}
              options={kbTypeOptions}
              value={answers.kb_type}
              onChange={(e) =>
                setAnswers((prev) => ({ ...prev, kb_type: e.target.value }))
              }
            />

            <div className="space-y-3">
              <ToggleQuestion
                checked={answers.has_tables_diagrams}
                onChange={() => handleToggle("has_tables_diagrams")}
                label={t("wizard.profile.questions.tables.label")}
                description={t("wizard.profile.questions.tables.description")}
              />
              <ToggleQuestion
                checked={answers.needs_multi_document}
                onChange={() => handleToggle("needs_multi_document")}
                label={t("wizard.profile.questions.multiDoc.label")}
                description={t("wizard.profile.questions.multiDoc.description")}
              />
              <ToggleQuestion
                checked={answers.large_documents}
                onChange={() => handleToggle("large_documents")}
                label={t("wizard.profile.questions.largeDocs.label")}
                description={t("wizard.profile.questions.largeDocs.description")}
              />
              <ToggleQuestion
                checked={answers.needs_precision}
                onChange={() => handleToggle("needs_precision")}
                label={t("wizard.profile.questions.precision.label")}
                description={t("wizard.profile.questions.precision.description")}
              />
              <ToggleQuestion
                checked={answers.frequent_updates}
                onChange={() => handleToggle("frequent_updates")}
                label={t("wizard.profile.questions.updates.label")}
                description={t("wizard.profile.questions.updates.description")}
              />
              <ToggleQuestion
                checked={answers.cite_page_numbers}
                onChange={() => handleToggle("cite_page_numbers")}
                label={t("wizard.profile.questions.citations.label")}
                description={t("wizard.profile.questions.citations.description")}
              />
            </div>
          </div>
        </CardContent>
        <CardFooter className="justify-between">
          <Button variant="ghost" onClick={onBack}>
            {t("common.actions.back")}
          </Button>
          <Button onClick={handleNext} isLoading={isAnalyzing}>
            {t("wizard.profile.analyze")}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}

function ToggleQuestion({
  checked,
  onChange,
  label,
  description,
}: {
  checked: boolean;
  onChange: () => void;
  label: string;
  description: string;
}) {
  return (
    <label className="flex items-start gap-3 p-3 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/60">
      <input
        type="checkbox"
        className="mt-1 h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
        checked={checked}
        onChange={onChange}
      />
      <div>
        <p className="font-medium text-gray-900 dark:text-white">{label}</p>
        <p className="text-sm text-gray-500 dark:text-gray-400">{description}</p>
      </div>
    </label>
  );
}
