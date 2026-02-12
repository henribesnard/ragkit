import { useState } from "react";
import { useTranslation } from "react-i18next";
import { FolderOpen } from "lucide-react";
import { Button, Card, CardContent, CardFooter, CardHeader, CardTitle, Input } from "../../components/ui";
import { ipc, type FolderValidationResult } from "../../lib/ipc";

export interface FolderSelection {
  path: string;
  recursive: boolean;
}

interface FolderStepProps {
  onNext: (folder: FolderSelection) => void;
  onBack: () => void;
  initialFolder?: FolderSelection | null;
}

export function FolderStep({ onNext, onBack, initialFolder }: FolderStepProps) {
  const { t } = useTranslation();
  const [path, setPath] = useState(initialFolder?.path || "");
  const [recursive, setRecursive] = useState(initialFolder?.recursive ?? true);
  const [validation, setValidation] = useState<FolderValidationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isValidating, setIsValidating] = useState(false);

  const mapValidationError = (result: FolderValidationResult) => {
    const code = result.error_code;
    if (!code) return result.error || t("wizard.folder.validation.generic");
    switch (code) {
      case "required":
        return t("wizard.folder.validation.required");
      case "not_exists":
        return t("wizard.folder.validation.notExists");
      case "not_dir":
        return t("wizard.folder.validation.notDir");
      case "no_permission":
        return t("wizard.folder.validation.noPermission");
      case "no_supported_files":
        return t("wizard.folder.validation.noSupported");
      case "scan_error":
        return t("wizard.folder.validation.scanError");
      default:
        return result.error || t("wizard.folder.validation.generic");
    }
  };

  const validateFolder = async (folderPath: string) => {
    const trimmed = folderPath.trim();
    if (!trimmed) {
      setValidation(null);
      setError(t("wizard.folder.validation.required"));
      return false;
    }

    setIsValidating(true);
    setError(null);
    try {
      const result = await ipc.validateFolder(trimmed);
      setValidation(result);
      if (!result.valid) {
        setError(mapValidationError(result));
        return false;
      }
      return true;
    } catch (err) {
      console.error("Folder validation failed:", err);
      setValidation(null);
      const detail = err instanceof Error ? err.message : String(err);
      setError(`${t("wizard.folder.validation.generic")} (${detail})`);
      return false;
    } finally {
      setIsValidating(false);
    }
  };

  const handleBrowse = async () => {
    try {
      const selected = await ipc.selectFolder();
      if (selected) {
        setPath(selected);
        await validateFolder(selected);
      }
    } catch (err) {
      console.error("Folder selection failed:", err);
      setError(t("wizard.folder.validation.browseFailed"));
    }
  };

  const handleNext = async () => {
    const isValid = await validateFolder(path);
    if (!isValid) return;
    onNext({ path: path.trim(), recursive });
  };

  const extensionSummary = validation?.stats?.extension_counts
    ? Object.entries(validation.stats.extension_counts)
      .map(([ext, count]) => `${ext.toUpperCase()} (${count})`)
      .join(", ")
    : validation?.stats?.extensions?.map((ext) => ext.toUpperCase()).join(", ");

  return (
    <div className="max-w-4xl mx-auto p-6">
      <Card>
        <CardHeader>
          <CardTitle>{t("wizard.folder.title")}</CardTitle>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {t("wizard.folder.subtitle")}
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
            <div className="flex-1">
              <Input
                label={t("wizard.folder.pathLabel")}
                value={path}
                onChange={(e) => {
                  setPath(e.target.value);
                  setError(null);
                  setValidation(null);
                }}
                placeholder={t("wizard.folder.placeholder")}
              />
            </div>
            <Button variant="secondary" onClick={handleBrowse}>
              <FolderOpen className="w-4 h-4 mr-2" />
              {t("common.actions.browse")}
            </Button>
          </div>

          <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
            <input
              type="checkbox"
              className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              checked={recursive}
              onChange={(e) => setRecursive(e.target.checked)}
            />
            {t("wizard.folder.includeSubfolders")}
          </label>

          {error && (
            <div className="rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 px-4 py-3 text-sm text-red-700 dark:text-red-300">
              {error}
            </div>
          )}

          {validation?.valid && (
            <div className="rounded-lg border border-emerald-200 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-900/20 px-4 py-3 text-sm text-emerald-700 dark:text-emerald-200">
              <p className="font-medium mb-2">{t("wizard.folder.stats.title")}</p>
              <div className="grid gap-2 sm:grid-cols-3 text-xs">
                <div>
                  <p className="uppercase text-emerald-600/80 dark:text-emerald-200/70">
                    {t("wizard.folder.stats.filesLabel")}
                  </p>
                  <p className="text-sm">
                    {t("wizard.folder.stats.files", { count: validation.stats.files })}
                  </p>
                </div>
                <div>
                  <p className="uppercase text-emerald-600/80 dark:text-emerald-200/70">
                    {t("wizard.folder.stats.sizeLabel")}
                  </p>
                  <p className="text-sm">
                    {t("wizard.folder.stats.sizeValue", { size: validation.stats.size_mb })}
                  </p>
                </div>
                <div>
                  <p className="uppercase text-emerald-600/80 dark:text-emerald-200/70">
                    {t("wizard.folder.stats.extensionsLabel")}
                  </p>
                  <p className="text-sm">
                    {extensionSummary || t("wizard.folder.stats.extensionsEmpty")}
                  </p>
                </div>
              </div>
            </div>
          )}

          <p className="text-sm text-gray-500 dark:text-gray-400">
            {t("wizard.folder.info")}
          </p>
        </CardContent>
        <CardFooter className="justify-between">
          <Button variant="ghost" onClick={onBack}>
            {t("common.actions.back")}
          </Button>
          <Button
            onClick={handleNext}
            isLoading={isValidating}
            disabled={!path.trim() || isValidating || !!error}
          >
            {t("common.actions.continue")}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
