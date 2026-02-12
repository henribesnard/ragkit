import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { CheckCircle } from "lucide-react";
import { Button, Card, CardContent, CardFooter, CardHeader, CardTitle } from "../../components/ui";
import type { FolderSelection } from "./FolderStep";
import type { ModelsSelection } from "./ModelsStep";
import type { ProfileResult } from "./ProfileStep";

interface SummaryStepProps {
  wizardData: {
    profile: ProfileResult | null;
    models: ModelsSelection | null;
    folder: FolderSelection | null;
  };
  onConfirm: () => void;
  onBack: () => void;
  isSubmitting?: boolean;
}

export function SummaryStep({ wizardData, onConfirm, onBack, isSubmitting }: SummaryStepProps) {
  const { t } = useTranslation();
  const profile = wizardData.profile?.analysis;
  const models = wizardData.models;
  const folder = wizardData.folder;

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{t("wizard.summary.title")}</CardTitle>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {t("wizard.summary.subtitle")}
          </p>
        </CardHeader>
        <CardContent className="space-y-6">
          <SummarySection title={t("wizard.summary.sections.profile")}>
            {profile ? (
              <div className="space-y-2">
                <p className="font-medium text-gray-900 dark:text-white">{profile.profile_name}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">{profile.description}</p>
                <div className="grid gap-2 sm:grid-cols-2">
                  {Object.entries(profile.config_summary || {}).map(([key, value]) => (
                    <div
                      key={key}
                      className="p-3 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/60"
                    >
                      <p className="text-xs uppercase text-gray-500 dark:text-gray-400">{key}</p>
                      <p className="text-sm text-gray-900 dark:text-white">{value}</p>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {t("wizard.summary.noProfile")}
              </p>
            )}
          </SummarySection>

          <SummarySection title={t("wizard.summary.sections.models")}>
            {models ? (
              <div className="grid gap-3 sm:grid-cols-2">
                <SummaryItem
                  label={t("wizard.summary.labels.embedding")}
                  value={`${models.embeddingProvider} · ${models.embeddingModel}`}
                />
                <SummaryItem
                  label={t("wizard.summary.labels.llm")}
                  value={`${models.llmProvider} · ${models.llmModel}`}
                />
              </div>
            ) : (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {t("wizard.summary.noModels")}
              </p>
            )}
          </SummarySection>

          <SummarySection title={t("wizard.summary.sections.documents")}>
            <SummaryItem
              label={t("wizard.summary.labels.folder")}
              value={folder?.path ? folder.path : t("wizard.summary.notSelected")}
            />
            {folder?.path ? (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {folder.recursive
                  ? t("wizard.summary.includeSubfolders")
                  : t("wizard.summary.topLevelOnly")}
              </p>
            ) : (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {t("wizard.summary.documentsLater")}
              </p>
            )}
          </SummarySection>
        </CardContent>
        <CardFooter className="justify-between">
          <Button variant="ghost" onClick={onBack}>
            {t("common.actions.back")}
          </Button>
          <Button onClick={onConfirm} isLoading={isSubmitting}>
            <CheckCircle className="w-4 h-4 mr-2" />
            {t("wizard.summary.finish")}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}

function SummarySection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide">
        {title}
      </h3>
      {children}
    </div>
  );
}

function SummaryItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-3 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/60">
      <p className="text-xs uppercase text-gray-500 dark:text-gray-400">{label}</p>
      <p className="text-sm text-gray-900 dark:text-white">{value}</p>
    </div>
  );
}
