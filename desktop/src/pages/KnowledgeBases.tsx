import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import {
  Plus,
  Trash2,
  Upload,
  FolderPlus,
  Database,
  FileText,
  Loader2,
  Clock,
  Layers,
} from "lucide-react";
import { ipc, KnowledgeBase } from "../lib/ipc";
import {
  Button,
  Input,
  Textarea,
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  Modal,
  ModalFooter,
  useConfirm,
  useToast,
} from "../components/ui";
import { cn, formatDate } from "../lib/utils";

const FOLDER_FILE_TYPES = [
  { value: "pdf", labelKey: "knowledgeBases.fileTypes.pdf" },
  { value: "txt", labelKey: "knowledgeBases.fileTypes.txt" },
  { value: "md", labelKey: "knowledgeBases.fileTypes.md" },
  { value: "docx", labelKey: "knowledgeBases.fileTypes.docx" },
  { value: "doc", labelKey: "knowledgeBases.fileTypes.doc" },
];

export function KnowledgeBases() {
  const { t } = useTranslation();
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [newKbName, setNewKbName] = useState("");
  const [newKbDescription, setNewKbDescription] = useState("");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [uploadingKbId, setUploadingKbId] = useState<string | null>(null);
  const [showAddFolderModal, setShowAddFolderModal] = useState(false);
  const [selectedKbForFolder, setSelectedKbForFolder] = useState<KnowledgeBase | null>(null);
  const [folderPath, setFolderPath] = useState("");
  const [folderRecursive, setFolderRecursive] = useState(true);
  const [folderFileTypes, setFolderFileTypes] = useState<string[]>([
    "pdf",
    "txt",
    "md",
    "docx",
    "doc",
  ]);
  const [isAddingFolder, setIsAddingFolder] = useState(false);
  const confirm = useConfirm();
  const toast = useToast();

  // Load knowledge bases
  useEffect(() => {
    loadKnowledgeBases();
  }, []);

  const loadKnowledgeBases = async () => {
    try {
      setIsLoading(true);
      const kbs = await ipc.listKnowledgeBases();
      setKnowledgeBases(kbs);
    } catch (error) {
      console.error("Failed to load knowledge bases:", error);
      toast.error(t("knowledgeBases.loadFailed"));
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!newKbName.trim()) return;

    try {
      setIsCreating(true);
      await ipc.createKnowledgeBase({
        name: newKbName.trim(),
        description: newKbDescription.trim() || undefined,
      });
      setNewKbName("");
      setNewKbDescription("");
      setShowCreateModal(false);
      loadKnowledgeBases();
    } catch (error) {
      console.error("Failed to create knowledge base:", error);
      toast.error(t("knowledgeBases.createFailed"));
    } finally {
      setIsCreating(false);
    }
  };

  const handleDelete = async (kb: KnowledgeBase) => {
    const confirmed = await confirm({
      title: t("knowledgeBases.confirmDeleteTitle"),
      message: t("knowledgeBases.confirmDeleteMessage", { name: kb.name }),
      confirmLabel: t("common.actions.delete"),
      cancelLabel: t("common.actions.cancel"),
      variant: "danger",
    });

    if (!confirmed) return;

    try {
      await ipc.deleteKnowledgeBase(kb.id);
      loadKnowledgeBases();
    } catch (error) {
      console.error("Failed to delete knowledge base:", error);
      toast.error(t("knowledgeBases.deleteFailed"));
    }
  };

  const handleAddDocuments = async (kb: KnowledgeBase) => {
    try {
      setUploadingKbId(kb.id);
      const files = await ipc.selectFiles();
      if (!files || files.length === 0) {
        setUploadingKbId(null);
        return;
      }

      await ipc.addDocuments(kb.id, files);
      loadKnowledgeBases();
    } catch (error) {
      console.error("Failed to add documents:", error);
    } finally {
      setUploadingKbId(null);
    }
  };

  const openAddFolderModal = (kb: KnowledgeBase) => {
    setSelectedKbForFolder(kb);
    setFolderPath("");
    setFolderRecursive(true);
    setFolderFileTypes(FOLDER_FILE_TYPES.map((item) => item.value));
    setShowAddFolderModal(true);
  };

  const handleSelectFolder = async () => {
    const folder = await ipc.selectFolder();
    if (folder) {
      setFolderPath(folder);
    }
  };

  const toggleFileType = (fileType: string) => {
    setFolderFileTypes((prev) =>
      prev.includes(fileType)
        ? prev.filter((item) => item !== fileType)
        : [...prev, fileType]
    );
  };

  const handleAddFolder = async () => {
    if (!selectedKbForFolder) return;
    if (!folderPath.trim()) {
      toast.error(t("knowledgeBases.folderRequiredTitle"), t("knowledgeBases.folderRequiredMessage"));
      return;
    }
    if (folderFileTypes.length === 0) {
      toast.error(t("knowledgeBases.selectFileTypesTitle"), t("knowledgeBases.selectFileTypesMessage"));
      return;
    }

    try {
      setIsAddingFolder(true);
      const result = await ipc.addFolder({
        kbId: selectedKbForFolder.id,
        folderPath,
        recursive: folderRecursive,
        fileTypes: folderFileTypes,
      });
      if (result.added.length === 0 && result.failed.length === 0) {
        toast.info(t("knowledgeBases.noDocumentsTitle"), t("knowledgeBases.noDocumentsMessage"));
      } else if (result.failed.length > 0) {
        toast.warning(
          t("knowledgeBases.folderIndexedWarningTitle"),
          t("knowledgeBases.folderIndexedWarningMessage", {
            added: result.added.length,
            failed: result.failed.length,
          })
        );
      } else {
        toast.success(
          t("knowledgeBases.folderIndexedTitle"),
          t("knowledgeBases.folderIndexedMessage", { count: result.added.length })
        );
      }
      setShowAddFolderModal(false);
      setFolderPath("");
      loadKnowledgeBases();
    } catch (error) {
      console.error("Failed to add folder:", error);
      toast.error(t("knowledgeBases.addFolderFailed"));
    } finally {
      setIsAddingFolder(false);
    }
  };

  const closeModal = () => {
    setShowCreateModal(false);
    setNewKbName("");
    setNewKbDescription("");
  };

  const closeAddFolderModal = () => {
    setShowAddFolderModal(false);
    setSelectedKbForFolder(null);
  };

  const addFolderTitle = selectedKbForFolder
    ? t("knowledgeBases.addFolderTitleWithName", { name: selectedKbForFolder.name })
    : t("knowledgeBases.addFolderTitle");

  return (
    <div className="h-full overflow-auto">
      {/* Header */}
      <header className="sticky top-0 z-10 flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
            <Database className="w-5 h-5 text-primary-600 dark:text-primary-400" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
              {t("knowledgeBases.title")}
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {t("knowledgeBases.count", { count: knowledgeBases.length })}
            </p>
          </div>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          <Plus className="w-4 h-4 mr-2" />
          {t("common.actions.create")}
        </Button>
      </header>

      {/* Content */}
      <div className="p-6">
        {isLoading ? (
          <LoadingState />
        ) : knowledgeBases.length === 0 ? (
          <EmptyState onCreateClick={() => setShowCreateModal(true)} />
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {knowledgeBases.map((kb) => (
              <KnowledgeBaseCard
                key={kb.id}
                kb={kb}
                isUploading={uploadingKbId === kb.id}
                onDelete={() => handleDelete(kb)}
                onAddDocuments={() => handleAddDocuments(kb)}
                onAddFolder={() => openAddFolderModal(kb)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Create Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={closeModal}
        title={t("knowledgeBases.createTitle")}
        description={t("knowledgeBases.createDescription")}
        size="md"
      >
        <div className="space-y-4">
          <Input
            label={t("knowledgeBases.nameLabel")}
            value={newKbName}
            onChange={(e) => setNewKbName(e.target.value)}
            placeholder={t("knowledgeBases.namePlaceholder")}
          />
          <Textarea
            label={t("knowledgeBases.descriptionLabel")}
            value={newKbDescription}
            onChange={(e) => setNewKbDescription(e.target.value)}
            placeholder={t("knowledgeBases.descriptionPlaceholder")}
            hint={t("knowledgeBases.descriptionHint")}
          />
        </div>
        <ModalFooter>
          <Button variant="secondary" onClick={closeModal}>
            {t("common.actions.cancel")}
          </Button>
          <Button
            onClick={handleCreate}
            disabled={!newKbName.trim()}
            isLoading={isCreating}
          >
            {t("common.actions.create")}
          </Button>
        </ModalFooter>
      </Modal>

      {/* Add Folder Modal */}
      <Modal
        isOpen={showAddFolderModal}
        onClose={closeAddFolderModal}
        title={addFolderTitle}
        description={t("knowledgeBases.addFolderDescription")}
        size="md"
      >
        <div className="space-y-4">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-end">
            <div className="flex-1">
              <Input
                label={t("knowledgeBases.folderPathLabel")}
                value={folderPath}
                onChange={(e) => setFolderPath(e.target.value)}
                placeholder={t("knowledgeBases.folderPathPlaceholder")}
              />
            </div>
            <Button variant="secondary" onClick={handleSelectFolder}>
              {t("common.actions.browse")}
            </Button>
          </div>

          <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
            <input
              type="checkbox"
              className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              checked={folderRecursive}
              onChange={(e) => setFolderRecursive(e.target.checked)}
            />
            {t("knowledgeBases.includeSubfolders")}
          </label>

          <div>
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {t("knowledgeBases.fileTypesLabel")}
            </p>
            <div className="grid gap-2 sm:grid-cols-2">
              {FOLDER_FILE_TYPES.map((fileType) => (
                <label
                  key={fileType.value}
                  className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400"
                >
                  <input
                    type="checkbox"
                    className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    checked={folderFileTypes.includes(fileType.value)}
                    onChange={() => toggleFileType(fileType.value)}
                  />
                  {t(fileType.labelKey)}
                </label>
              ))}
            </div>
          </div>
        </div>
        <ModalFooter>
          <Button variant="secondary" onClick={closeAddFolderModal}>
            {t("common.actions.cancel")}
          </Button>
          <Button
            onClick={handleAddFolder}
            disabled={!folderPath.trim() || folderFileTypes.length === 0}
            isLoading={isAddingFolder}
          >
            {t("knowledgeBases.addFolderButton")}
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
}

// Loading state
function LoadingState() {
  const { t } = useTranslation();
  return (
    <div className="flex flex-col items-center justify-center py-16">
      <Loader2 className="w-10 h-10 text-primary-600 animate-spin" />
      <p className="mt-4 text-gray-500 dark:text-gray-400">
        {t("knowledgeBases.loading")}
      </p>
    </div>
  );
}

// Empty state
function EmptyState({ onCreateClick }: { onCreateClick: () => void }) {
  const { t } = useTranslation();
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-800 dark:to-gray-700 flex items-center justify-center mb-6 shadow-lg">
        <Database className="w-10 h-10 text-gray-400 dark:text-gray-500" />
      </div>
      <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">
        {t("knowledgeBases.emptyTitle")}
      </h2>
      <p className="mt-3 text-gray-600 dark:text-gray-400 max-w-md text-lg">
        {t("knowledgeBases.emptyDescription")}
      </p>
      <Button onClick={onCreateClick} className="mt-6" size="lg">
        <Plus className="w-5 h-5 mr-2" />
        {t("knowledgeBases.emptyCta")}
      </Button>
    </div>
  );
}

// Knowledge Base Card
function KnowledgeBaseCard({
  kb,
  isUploading,
  onDelete,
  onAddDocuments,
  onAddFolder,
}: {
  kb: KnowledgeBase;
  isUploading: boolean;
  onDelete: () => void;
  onAddDocuments: () => void;
  onAddFolder: () => void;
}) {
  const { t } = useTranslation();
  return (
    <Card className="hover:shadow-lg transition-shadow duration-200">
      <CardHeader
        action={
          <Button
            variant="ghost"
            size="icon"
            onClick={onDelete}
            className="h-8 w-8 text-gray-400 hover:text-red-500"
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        }
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center flex-shrink-0">
            <Database className="w-5 h-5 text-primary-600 dark:text-primary-400" />
          </div>
          <div className="min-w-0">
            <CardTitle>{kb.name}</CardTitle>
            {kb.description && (
              <CardDescription className="line-clamp-1">
                {kb.description}
              </CardDescription>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {/* Stats */}
        <div className="grid grid-cols-2 gap-3">
          <StatBadge
            icon={FileText}
            label={t("knowledgeBases.stats.documents")}
            value={kb.document_count}
            color="blue"
          />
          <StatBadge
            icon={Layers}
            label={t("knowledgeBases.stats.chunks")}
            value={kb.chunk_count}
            color="green"
          />
        </div>

        {/* Metadata */}
        <div className="mt-4 flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
          <span className="flex items-center gap-1">
            <span className="font-medium">{t("knowledgeBases.modelLabel")}</span> {kb.embedding_model}
          </span>
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {formatDate(kb.updated_at)}
          </span>
        </div>
      </CardContent>

      <CardFooter className="pt-3 mt-3">
        <div className="flex w-full gap-2">
          <Button
            variant="secondary"
            className="flex-1"
            onClick={onAddDocuments}
            isLoading={isUploading}
          >
            <Upload className="w-4 h-4 mr-2" />
            {t("knowledgeBases.addDocuments")}
          </Button>
          <Button variant="secondary" className="flex-1" onClick={onAddFolder}>
            <FolderPlus className="w-4 h-4 mr-2" />
            {t("knowledgeBases.addFolder")}
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
}

// Stat badge component
function StatBadge({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: typeof FileText;
  label: string;
  value: number;
  color: "blue" | "green" | "yellow" | "red";
}) {
  const colors = {
    blue: "bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400",
    green: "bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400",
    yellow: "bg-yellow-50 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-400",
    red: "bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400",
  };

  return (
    <div className={cn("flex items-center gap-2 px-3 py-2 rounded-lg", colors[color])}>
      <Icon className="w-4 h-4" />
      <div>
        <p className="text-lg font-semibold">{value}</p>
        <p className="text-xs opacity-80">{label}</p>
      </div>
    </div>
  );
}
