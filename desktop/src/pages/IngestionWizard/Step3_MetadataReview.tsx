import { useState, useEffect } from "react";
import { ipc } from "../../lib/ipc"; // We will need a new endpoint to get files by type
import { useTranslation } from "react-i18next";
import { Loader2 } from "lucide-react";

interface Step3Props {
    selectedTypes: string[];
    sourcePath: string;
    recursive: boolean;
    onNext: (files: any[]) => void;
    onBack: () => void;
}

// Placeholder for the file data structure
interface FileMetadata {
    path: string;
    name: string;
    type: string;
    title: string;
    author: string;
    tags: string[];
    // Technical fields (hidden)
    size: number;
}

export function Step3_MetadataReview({ selectedTypes, sourcePath, recursive, onNext, onBack }: Step3Props) {
    const { t } = useTranslation();
    const [isLoading, setIsLoading] = useState(true);
    const [files, setFiles] = useState<FileMetadata[]>([]);
    const [error, setError] = useState<string | null>(null);

    // Simulation of fetching files based on types
    // In a real implementation, we would call a backend endpoint like `ipc.getFilesByTypes(path, recursive, selectedTypes)`
    // For now, we will simulate this or use scanResult if we passed it (but scanResult only had stats)
    // We need to implement `get_files_by_type` in backend or just use `scan` result if it contained all files.
    // The `scan_directory` endpoint actually returned `files` list in `scanResult`.
    // So we might strictly need to pass `scanResult` to this step too, or just filter safely.

    // Let's assume we need to filter `scanResult` files if we had them, OR fetch details.
    // `ScanDirectoryResponse` has `files: any[]`.
    // Let's rely on the parent simulation for now or implements a mock fetch.

    useEffect(() => {
        async function loadFiles() {
            // In a real app, we might re-scan to get clean list or filter existing.
            // For this prototype, we will simulate "loading" and metadata extraction defaults.
            setIsLoading(true);
            try {
                // TODO: Replace with actual backend call to get detailed metadata for selected types
                // const result = await ipc.getFilesDetails(sourcePath, selectedTypes);

                // Simulating delay for "Metadata Extraction"
                await new Promise(r => setTimeout(r, 800));

                // Mock data generation
                const mockFiles: FileMetadata[] = selectedTypes.flatMap(type => {
                    return Array.from({ length: 3 }).map((_, i) => ({
                        path: `${sourcePath}/doc_${type}_${i}.${type}`,
                        name: `doc_${type}_${i}.${type}`,
                        type: type,
                        title: `Document ${type.toUpperCase()} ${i + 1}`,
                        author: "Unknown",
                        tags: ["draft"],
                        size: 1024 * (i + 1)
                    }));
                });
                setFiles(mockFiles);
            } catch (e) {
                setError("Failed to load file metadata.");
                console.error(e);
            } finally {
                setIsLoading(false);
            }
        }
        loadFiles();
    }, [selectedTypes, sourcePath]);


    const updateFileMetadata = (path: string, field: keyof FileMetadata, value: any) => {
        setFiles(prev => prev.map(f => f.path === path ? { ...f, [field]: value } : f));
    };

    const handleTagsChange = (path: string, tagsString: string) => {
        const tags = tagsString.split(",").map(t => t.trim()).filter(Boolean);
        updateFileMetadata(path, "tags", tags);
    };

    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center h-64 text-gray-500">
                <Loader2 className="w-8 h-8 animate-spin mb-4 text-primary-600" />
                <p>{t("ingestion.extractingMetadata", "Extracting default metadata...")}</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="text-center text-red-500 mt-10">
                <p>{error}</p>
                <button onClick={onBack} className="mt-4 underline">Go Back</button>
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-6 max-w-6xl mx-auto mt-4 text-gray-900 dark:text-gray-100 pb-20">
            <div className="text-center">
                <h2 className="text-2xl font-bold">
                    {t("ingestion.step3.title", "Review Metadata")}
                </h2>
                <p className="text-gray-500 dark:text-gray-400 mt-2">
                    {t("ingestion.step3.subtitle", "Review and edit functional metadata before ingestion.")}
                </p>
            </div>

            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                        <thead className="bg-gray-50 dark:bg-gray-900 text-gray-700 dark:text-gray-300 font-medium">
                            <tr>
                                <th className="px-6 py-3">File</th>
                                <th className="px-6 py-3">Title</th>
                                <th className="px-6 py-3">Author</th>
                                <th className="px-6 py-3">Tags (comma separated)</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                            {files.map(file => (
                                <tr key={file.path} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                                    <td className="px-6 py-4 font-medium text-gray-900 dark:text-white max-w-xs truncate" title={file.path}>
                                        {file.name}
                                        <div className="text-xs text-gray-500 font-normal">{file.type.toUpperCase()}</div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <input
                                            type="text"
                                            value={file.title}
                                            onChange={(e) => updateFileMetadata(file.path, "title", e.target.value)}
                                            className="w-full px-2 py-1 bg-transparent border-b border-transparent hover:border-gray-300 focus:border-primary-500 focus:outline-none transition-colors"
                                        />
                                    </td>
                                    <td className="px-6 py-4">
                                        <input
                                            type="text"
                                            value={file.author}
                                            onChange={(e) => updateFileMetadata(file.path, "author", e.target.value)}
                                            className="w-full px-2 py-1 bg-transparent border-b border-transparent hover:border-gray-300 focus:border-primary-500 focus:outline-none transition-colors"
                                        />
                                    </td>
                                    <td className="px-6 py-4">
                                        <input
                                            type="text"
                                            defaultValue={file.tags.join(", ")}
                                            onBlur={(e) => handleTagsChange(file.path, e.target.value)}
                                            className="w-full px-2 py-1 bg-transparent border-b border-transparent hover:border-gray-300 focus:border-primary-500 focus:outline-none transition-colors"
                                            placeholder="Add tags..."
                                        />
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Navigation */}
            <div className="flex justify-between pt-4">
                <button
                    onClick={onBack}
                    className="px-6 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                    ← {t("common.back", "Back")}
                </button>
                <button
                    onClick={() => onNext(files)}
                    className="px-6 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-md font-medium transition-colors"
                >
                    {t("common.next", "Next")} →
                </button>
            </div>
        </div>
    );
}
