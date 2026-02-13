import { useState, useMemo } from "react";
import { ScanDirectoryResponse } from "../../lib/ipc";
import { useTranslation } from "react-i18next";
import { FileText, Check, AlertTriangle } from "lucide-react";

interface Step2Props {
    scanResult: ScanDirectoryResponse;
    onNext: (selectedTypes: string[]) => void;
    onBack: () => void;
    initialSelectedTypes?: string[];
}

export function Step2_Analysis({ scanResult, onNext, onBack, initialSelectedTypes }: Step2Props) {
    const { t } = useTranslation();

    // Extract available types from scan result
    const availableTypes = useMemo(() => {
        return Object.keys(scanResult.stats_by_type);
    }, [scanResult]);

    // State
    const [selectedTypes, setSelectedTypes] = useState<string[]>(
        initialSelectedTypes || availableTypes
    );

    const toggleType = (type: string) => {
        if (selectedTypes.includes(type)) {
            setSelectedTypes(selectedTypes.filter(t => t !== type));
        } else {
            setSelectedTypes([...selectedTypes, type]);
        }
    };

    const handleNext = () => {
        onNext(selectedTypes);
    };

    const totalSelectedFiles = useMemo(() => {
        return selectedTypes.reduce((acc, type) => {
            return acc + (scanResult.stats_by_type[type]?.count || 0);
        }, 0);
    }, [selectedTypes, scanResult]);

    const totalSelectedSize = useMemo(() => {
        const bytes = selectedTypes.reduce((acc, type) => {
            return acc + (scanResult.stats_by_type[type]?.size || 0);
        }, 0);
        return (bytes / 1024 / 1024).toFixed(2); // MB
    }, [selectedTypes, scanResult]);

    return (
        <div className="flex flex-col gap-6 max-w-4xl mx-auto mt-10 text-gray-900 dark:text-gray-100 pb-20">
            <div className="text-center">
                <h2 className="text-2xl font-bold">
                    {t("ingestion.step2.title", "Analysis & Filtering")}
                </h2>
                <p className="text-gray-500 dark:text-gray-400 mt-2">
                    {t("ingestion.step2.subtitle", "Review detected files and select types to ingest.")}
                </p>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm flex items-center gap-4">
                    <div className="p-3 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-full">
                        <FileText size={24} />
                    </div>
                    <div>
                        <p className="text-sm text-gray-500 dark:text-gray-400">Total Files</p>
                        <p className="text-2xl font-bold">{scanResult.total_files}</p>
                    </div>
                </div>

                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm flex items-center gap-4">
                    <div className="p-3 bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 rounded-full">
                        <Check size={24} />
                    </div>
                    <div>
                        <p className="text-sm text-gray-500 dark:text-gray-400">Selected for Ingestion</p>
                        <p className="text-2xl font-bold">{totalSelectedFiles}</p>
                    </div>
                </div>

                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm flex items-center gap-4">
                    <div className="p-3 bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 rounded-full">
                        <Database size={24} /> {/* Using Database icon or similar for size */}
                    </div>
                    <div>
                        <p className="text-sm text-gray-500 dark:text-gray-400">Estimated Size</p>
                        <p className="text-2xl font-bold">{totalSelectedSize} MB</p>
                    </div>
                </div>
            </div>

            {/* Type Selection List */}
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50 flex justify-between items-center">
                    <h3 className="font-semibold">{t("ingestion.detectedTypes", "Detected File Types")}</h3>
                    <span className="text-xs font-mono bg-gray-200 dark:bg-gray-700 px-2 py-1 rounded">
                        {availableTypes.length} types
                    </span>
                </div>

                <div className="divide-y divide-gray-200 dark:divide-gray-700">
                    {availableTypes.length === 0 ? (
                        <div className="p-8 text-center text-gray-500">
                            <AlertTriangle className="mx-auto h-8 w-8 text-yellow-500 mb-2" />
                            <p>{t("ingestion.noFilesFound", "No supported files found in this directory.")}</p>
                        </div>
                    ) : (
                        availableTypes.map(type => {
                            const stats = scanResult.stats_by_type[type];
                            const isSelected = selectedTypes.includes(type);

                            return (
                                <div
                                    key={type}
                                    className={`px-6 py-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors cursor-pointer ${isSelected ? 'bg-primary-50/50 dark:bg-primary-900/10' : ''}`}
                                    onClick={() => toggleType(type)}
                                >
                                    <div className="flex items-center gap-4">
                                        <input
                                            type="checkbox"
                                            checked={isSelected}
                                            onChange={() => toggleType(type)}
                                            className="w-5 h-5 text-primary-600 rounded border-gray-300 focus:ring-primary-500 dark:border-gray-600 dark:bg-gray-700"
                                        />
                                        <div>
                                            <span className="font-medium uppercase">{type}</span>
                                            <span className="text-gray-500 dark:text-gray-400 text-sm ml-2">
                                                ({stats.count} files)
                                            </span>
                                        </div>
                                    </div>
                                    <div className="text-sm text-gray-500 dark:text-gray-400">
                                        {(stats.size / 1024 / 1024).toFixed(2)} MB
                                    </div>
                                </div>
                            );
                        })
                    )}
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
                    onClick={handleNext}
                    disabled={selectedTypes.length === 0}
                    className="px-6 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-md font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {t("common.next", "Next")} →
                </button>
            </div>
        </div>
    );
}

// Helper icon component if needed, or import from lucide-react
function Database(props: any) {
    return (
        <svg
            {...props}
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
        >
            <ellipse cx="12" cy="5" rx="9" ry="3" />
            <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
            <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
        </svg>
    );
}
