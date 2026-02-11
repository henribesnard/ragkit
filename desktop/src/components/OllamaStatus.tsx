import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import {
  Server,
  Download,
  Trash2,
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertCircle,
  Play,
  ExternalLink,
  Loader2,
  HardDrive,
} from "lucide-react";
import { ipc, OllamaStatus as OllamaStatusType, OllamaModel, RecommendedModel } from "../lib/ipc";
import {
  Button,
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  Modal,
  ModalFooter,
  useToast,
  useConfirm,
} from "./ui";
import { cn } from "../lib/utils";

export function OllamaStatusCard() {
  const { t } = useTranslation();
  const toast = useToast();
  const confirm = useConfirm();
  const [status, setStatus] = useState<OllamaStatusType | null>(null);
  const [models, setModels] = useState<OllamaModel[]>([]);
  const [recommended, setRecommended] = useState<Record<string, RecommendedModel>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isStarting, setIsStarting] = useState(false);
  const [isPulling, setIsPulling] = useState<string | null>(null);
  const [showInstallModal, setShowInstallModal] = useState(false);
  const [installInstructions, setInstallInstructions] = useState<string>("");

  const loadStatus = async () => {
    try {
      const [statusData, modelsData, recommendedData] = await Promise.all([
        ipc.getOllamaStatus(),
        ipc.listOllamaModels().catch(() => []),
        ipc.getRecommendedModels().catch(() => ({})),
      ]);
      setStatus(statusData);
      setModels(modelsData);
      setRecommended(recommendedData);
    } catch (error) {
      console.error("Failed to load Ollama status:", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadStatus();
    // Refresh every 30 seconds
    const interval = setInterval(loadStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleStartService = async () => {
    setIsStarting(true);
    try {
      await ipc.startOllamaService();
      toast.success(t("ollama.toasts.startedTitle"), t("ollama.toasts.startedMessage"));
      await loadStatus();
    } catch (error) {
      toast.error(t("ollama.toasts.startFailedTitle"), String(error));
    } finally {
      setIsStarting(false);
    }
  };

  const handlePullModel = async (modelName: string) => {
    setIsPulling(modelName);
    try {
      toast.info(
        t("ollama.toasts.downloadingTitle"),
        t("ollama.toasts.downloadingMessage", { model: modelName })
      );
      await ipc.pullOllamaModel(modelName);
      toast.success(
        t("ollama.toasts.downloadedTitle"),
        t("ollama.toasts.downloadedMessage", { model: modelName })
      );
      await loadStatus();
    } catch (error) {
      toast.error(t("ollama.toasts.downloadFailedTitle"), String(error));
    } finally {
      setIsPulling(null);
    }
  };

  const handleDeleteModel = async (modelName: string) => {
    const confirmed = await confirm({
      title: t("ollama.confirmDeleteTitle"),
      message: t("ollama.confirmDeleteMessage", { model: modelName }),
      confirmLabel: t("common.actions.delete"),
      cancelLabel: t("common.actions.cancel"),
      variant: "danger",
    });

    if (!confirmed) return;

    try {
      await ipc.deleteOllamaModel(modelName);
      toast.success(
        t("ollama.toasts.deleteSuccessTitle"),
        t("ollama.toasts.deleteSuccessMessage", { model: modelName })
      );
      await loadStatus();
    } catch (error) {
      toast.error(t("ollama.toasts.deleteFailedTitle"), String(error));
    }
  };

  const handleShowInstall = async () => {
    try {
      const instructions = await ipc.getInstallInstructions();
      setInstallInstructions(instructions.instructions);
      setShowInstallModal(true);
    } catch (error) {
      console.error("Failed to get install instructions:", error);
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="flex items-center justify-center">
            <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
          </div>
        </CardContent>
      </Card>
    );
  }

  const installedModelNames = models.map((m) => m.name.split(":")[0]);

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div
                className={cn(
                  "w-10 h-10 rounded-lg flex items-center justify-center",
                  status?.running
                    ? "bg-green-100 dark:bg-green-900/30"
                    : status?.installed
                    ? "bg-yellow-100 dark:bg-yellow-900/30"
                    : "bg-red-100 dark:bg-red-900/30"
                )}
              >
                <Server
                  className={cn(
                    "w-5 h-5",
                    status?.running
                      ? "text-green-600 dark:text-green-400"
                      : status?.installed
                      ? "text-yellow-600 dark:text-yellow-400"
                      : "text-red-600 dark:text-red-400"
                  )}
                />
              </div>
              <div>
                <CardTitle>{t("ollama.title")}</CardTitle>
                <CardDescription>
                  {status?.running
                    ? t("ollama.status.runningVersion", {
                        version: status.version || "?",
                      })
                    : status?.installed
                    ? t("ollama.status.notRunning")
                    : t("ollama.status.notInstalled")}
                </CardDescription>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <StatusBadge status={status} />
              <Button
                variant="ghost"
                size="icon"
                onClick={loadStatus}
                className="h-8 w-8"
              >
                <RefreshCw className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          {/* Not Installed */}
          {!status?.installed && (
            <div className="text-center py-6">
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                {t("ollama.install.required")}
              </p>
              <Button onClick={handleShowInstall}>
                <ExternalLink className="w-4 h-4 mr-2" />
                {t("ollama.install.cta")}
              </Button>
            </div>
          )}

          {/* Installed but not running */}
          {status?.installed && !status?.running && (
            <div className="text-center py-6">
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                {t("ollama.install.notRunning")}
              </p>
              <Button onClick={handleStartService} isLoading={isStarting}>
                <Play className="w-4 h-4 mr-2" />
                {t("ollama.install.start")}
              </Button>
            </div>
          )}

          {/* Running - Show models */}
          {status?.running && (
            <div className="space-y-6">
              {/* Installed Models */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  {t("ollama.models.installed", { count: models.length })}
                </h4>
                {models.length === 0 ? (
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {t("ollama.models.none")}
                  </p>
                ) : (
                  <div className="space-y-2">
                    {models.map((model) => (
                      <div
                        key={model.name}
                        className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50"
                      >
                        <div className="flex items-center gap-3">
                          <HardDrive className="w-4 h-4 text-gray-400" />
                          <div>
                            <p className="font-medium text-gray-900 dark:text-white">
                              {model.name}
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                              {model.size_formatted}
                            </p>
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteModel(model.name)}
                          className="text-red-500 hover:text-red-600"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Recommended Models */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  {t("ollama.models.recommended")}
                </h4>
                <div className="grid gap-2">
                  {Object.entries(recommended).map(([id, model]) => {
                    const isInstalled = installedModelNames.includes(id.split(":")[0]);
                    const isDownloading = isPulling === id;

                    return (
                      <div
                        key={id}
                        className={cn(
                          "flex items-center justify-between p-3 rounded-lg border transition-colors",
                          isInstalled
                            ? "border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/10"
                            : "border-gray-200 dark:border-gray-700"
                        )}
                      >
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <p className="font-medium text-gray-900 dark:text-white">
                              {model.name}
                            </p>
                            <QualityBadge quality={model.quality} />
                            <SpeedBadge speed={model.speed} />
                          </div>
                          <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                            {model.description} ({model.size})
                          </p>
                        </div>
                        {isInstalled ? (
                          <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
                        ) : (
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => handlePullModel(id)}
                            isLoading={isDownloading}
                            disabled={isPulling !== null}
                          >
                            <Download className="w-4 h-4 mr-1" />
                            {t("ollama.models.download")}
                          </Button>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Install Instructions Modal */}
      <Modal
        isOpen={showInstallModal}
        onClose={() => setShowInstallModal(false)}
        title={t("ollama.install.modalTitle")}
        description={t("ollama.install.modalDescription")}
        size="md"
      >
        <div className="space-y-4">
          <pre className="p-4 rounded-lg bg-gray-100 dark:bg-gray-800 text-sm font-mono overflow-x-auto">
            {installInstructions}
          </pre>
          <a
            href="https://ollama.ai"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center text-primary-600 hover:text-primary-700 dark:text-primary-400"
          >
            {t("ollama.install.visitSite")}
            <ExternalLink className="w-4 h-4 ml-1" />
          </a>
        </div>
        <ModalFooter>
          <Button variant="secondary" onClick={() => setShowInstallModal(false)}>
            {t("common.actions.close")}
          </Button>
          <Button onClick={loadStatus}>
            <RefreshCw className="w-4 h-4 mr-2" />
            {t("ollama.install.checkAgain")}
          </Button>
        </ModalFooter>
      </Modal>
    </>
  );
}

// Status badge component
function StatusBadge({ status }: { status: OllamaStatusType | null }) {
  const { t } = useTranslation();
  if (!status) return null;

  if (status.running) {
    return (
      <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-xs font-medium">
        <CheckCircle className="w-3 h-3" />
        {t("ollama.status.running")}
      </div>
    );
  }

  if (status.installed) {
    return (
      <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 text-xs font-medium">
        <AlertCircle className="w-3 h-3" />
        {t("ollama.status.stopped")}
      </div>
    );
  }

  return (
    <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 text-xs font-medium">
      <XCircle className="w-3 h-3" />
      {t("ollama.status.notInstalled")}
    </div>
  );
}

// Quality badge
function QualityBadge({ quality }: { quality: string }) {
  const { t } = useTranslation();
  const colors = {
    good: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
    excellent: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400",
  };

  return (
    <span
      className={cn(
        "px-1.5 py-0.5 rounded text-xs font-medium",
        colors[quality as keyof typeof colors] || colors.good
      )}
    >
      {t(`ollama.quality.${quality}`)}
    </span>
  );
}

// Speed badge
function SpeedBadge({ speed }: { speed: string }) {
  const { t } = useTranslation();
  return (
    <span className="px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 text-xs">
      {t(`ollama.speed.${speed}`)}
    </span>
  );
}
