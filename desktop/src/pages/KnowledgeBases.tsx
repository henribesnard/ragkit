import { useState, useEffect } from "react";
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
  { value: "pdf", label: "PDF" },
  { value: "txt", label: "Text" },
  { value: "md", label: "Markdown" },
  { value: "docx", label: "Word (.docx)" },
  { value: "doc", label: "Word (.doc)" },
];

export function KnowledgeBases() {
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
    } finally {
      setIsCreating(false);
    }
  };

  const handleDelete = async (kb: KnowledgeBase) => {
    const confirmed = await confirm({
      title: "Delete Knowledge Base",
      message: `Are you sure you want to delete "${kb.name}"? This action cannot be undone and all documents will be permanently removed.`,
      confirmLabel: "Delete",
      cancelLabel: "Cancel",
      variant: "danger",
    });

    if (!confirmed) return;

    try {
      await ipc.deleteKnowledgeBase(kb.id);
      loadKnowledgeBases();
    } catch (error) {
      console.error("Failed to delete knowledge base:", error);
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
      toast.error("Folder required", "Please choose a folder to import.");
      return;
    }
    if (folderFileTypes.length === 0) {
      toast.error("Select file types", "Choose at least one file type.");
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
        toast.info("No documents found", "No matching files were detected.");
      } else if (result.failed.length > 0) {
        toast.warning(
          "Folder indexed with warnings",
          `${result.added.length} added, ${result.failed.length} failed.`
        );
      } else {
        toast.success(
          "Folder indexed",
          `${result.added.length} document${result.added.length !== 1 ? "s" : ""} added.`
        );
      }
      setShowAddFolderModal(false);
      setFolderPath("");
      loadKnowledgeBases();
    } catch (error) {
      console.error("Failed to add folder:", error);
      toast.error("Failed to add folder");
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
              Knowledge Bases
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {knowledgeBases.length} knowledge base{knowledgeBases.length !== 1 ? "s" : ""}
            </p>
          </div>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Create
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
        title="Create Knowledge Base"
        description="Create a new knowledge base to store and query your documents."
        size="md"
      >
        <div className="space-y-4">
          <Input
            label="Name"
            value={newKbName}
            onChange={(e) => setNewKbName(e.target.value)}
            placeholder="My Knowledge Base"
          />
          <Textarea
            label="Description (optional)"
            value={newKbDescription}
            onChange={(e) => setNewKbDescription(e.target.value)}
            placeholder="A brief description of what this knowledge base contains..."
            hint="This helps you remember what documents are stored here."
          />
        </div>
        <ModalFooter>
          <Button variant="secondary" onClick={closeModal}>
            Cancel
          </Button>
          <Button
            onClick={handleCreate}
            disabled={!newKbName.trim()}
            isLoading={isCreating}
          >
            Create
          </Button>
        </ModalFooter>
      </Modal>

      {/* Add Folder Modal */}
      <Modal
        isOpen={showAddFolderModal}
        onClose={closeAddFolderModal}
        title={`Add Folder${selectedKbForFolder ? ` to ${selectedKbForFolder.name}` : ""}`}
        description="Import all documents from a folder into this knowledge base."
        size="md"
      >
        <div className="space-y-4">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-end">
            <div className="flex-1">
              <Input
                label="Folder path"
                value={folderPath}
                onChange={(e) => setFolderPath(e.target.value)}
                placeholder="Select a folder..."
              />
            </div>
            <Button variant="secondary" onClick={handleSelectFolder}>
              Browse
            </Button>
          </div>

          <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
            <input
              type="checkbox"
              className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              checked={folderRecursive}
              onChange={(e) => setFolderRecursive(e.target.checked)}
            />
            Include subfolders
          </label>

          <div>
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              File types
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
                  {fileType.label}
                </label>
              ))}
            </div>
          </div>
        </div>
        <ModalFooter>
          <Button variant="secondary" onClick={closeAddFolderModal}>
            Cancel
          </Button>
          <Button
            onClick={handleAddFolder}
            disabled={!folderPath.trim() || folderFileTypes.length === 0}
            isLoading={isAddingFolder}
          >
            Add Folder
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
}

// Loading state
function LoadingState() {
  return (
    <div className="flex flex-col items-center justify-center py-16">
      <Loader2 className="w-10 h-10 text-primary-600 animate-spin" />
      <p className="mt-4 text-gray-500 dark:text-gray-400">Loading knowledge bases...</p>
    </div>
  );
}

// Empty state
function EmptyState({ onCreateClick }: { onCreateClick: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-800 dark:to-gray-700 flex items-center justify-center mb-6 shadow-lg">
        <Database className="w-10 h-10 text-gray-400 dark:text-gray-500" />
      </div>
      <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">
        No knowledge bases yet
      </h2>
      <p className="mt-3 text-gray-600 dark:text-gray-400 max-w-md text-lg">
        Create your first knowledge base to start indexing documents and querying them with AI.
      </p>
      <Button onClick={onCreateClick} className="mt-6" size="lg">
        <Plus className="w-5 h-5 mr-2" />
        Create Knowledge Base
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
            label="Documents"
            value={kb.document_count}
            color="blue"
          />
          <StatBadge
            icon={Layers}
            label="Chunks"
            value={kb.chunk_count}
            color="green"
          />
        </div>

        {/* Metadata */}
        <div className="mt-4 flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
          <span className="flex items-center gap-1">
            <span className="font-medium">Model:</span> {kb.embedding_model}
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
            Add Documents
          </Button>
          <Button variant="secondary" className="flex-1" onClick={onAddFolder}>
            <FolderPlus className="w-4 h-4 mr-2" />
            Add Folder
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
