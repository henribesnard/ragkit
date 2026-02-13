import { useState } from "react";
import { ipc } from "../../lib/ipc";
import { useTranslation } from "react-i18next";
import { FolderOpen } from "lucide-react";

interface Step1Props {
    onNext: (path: string, recursive: boolean) => void;
    initialPath?: string;
    initialRecursive?: boolean;
}

export function Step1_SourceSelection({ onNext, initialPath = "", initialRecursive = true }: Step1Props) {
    const { t } = useTranslation();
    const [path, setPath] = useState(initialPath);
    const [recursive, setRecursive] = useState(initialRecursive);
    const [isLoading, setIsLoading] = useState(false);

    const handleBrowse = async () => {
        try {
            setIsLoading(true);
            const selected = await ipc.selectFolder();
            if (selected) {
                setPath(selected);
            }
        } catch (error) {
            console.error("Failed to select folder:", error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleNext = () => {
        if (path) {
            onNext(path, recursive);
        }
    };

    return (
        <div className="flex flex-col gap-6 max-w-2xl mx-auto mt-10">
            <div className="text-center">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                    {t("ingestion.step1.title", "Select Source Directory")}
                </h2>
                <p className="text-gray-500 dark:text-gray-400 mt-2">
                    {t("ingestion.step1.subtitle", "Choose the folder containing your documents.")}
                </p>
            </div>

            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm">
                <div className="flex flex-col gap-4">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                        {t("ingestion.directoryPath", "Directory Path")}
                    </label>
                    <div className="flex gap-2">
                        <input
                            type="text"
                            value={path}
                            readOnly
                            className="flex-1 px-4 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white cursor-not-allowed"
                            placeholder={t("ingestion.selectPlaceholder", "No folder selected...")}
                        />
                        <button
                            onClick={handleBrowse}
                            disabled={isLoading}
                            className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-md transition-colors disabled:opacity-50"
                        >
                            <FolderOpen size={18} />
                            {t("common.browse", "Browse")}
                        </button>
                    </div>

                    <div className="flex items-center gap-2 mt-2">
                        <input
                            type="checkbox"
                            id="recursive"
                            checked={recursive}
                            onChange={(e) => setRecursive(e.target.checked)}
                            className="w-4 h-4 text-primary-600 rounded border-gray-300 focus:ring-primary-500 dark:border-gray-600 dark:bg-gray-700"
                        />
                        <label htmlFor="recursive" className="text-sm text-gray-700 dark:text-gray-300 cursor-pointer select-none">
                            {t("ingestion.includeSubfolders", "Include subfolders")}
                        </label>
                    </div>
                </div>
            </div>

            <div className="flex justify-end">
                <button
                    onClick={handleNext}
                    disabled={!path}
                    className="px-6 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-md font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {t("common.next", "Next")} →
                </button>
            </div>
        </div>
    );
}
