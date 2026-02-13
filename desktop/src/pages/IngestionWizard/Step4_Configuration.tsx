import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Settings, Play } from "lucide-react";

interface Step4Props {
    filesCount: number;
    onBack: () => void;
    onStartIngestion: (config: IngestionConfig) => void;
}

export interface IngestionConfig {
    chunkSize: number;
    chunkOverlap: number;
    useOcr: boolean;
    ocrLanguage: string;
    parsingEngine: "default" | "advanced";
}

export function Step4_Configuration({ filesCount, onBack, onStartIngestion }: Step4Props) {
    const { t } = useTranslation();

    const [config, setConfig] = useState<IngestionConfig>({
        chunkSize: 1000,
        chunkOverlap: 200,
        useOcr: false,
        ocrLanguage: "eng+fra",
        parsingEngine: "default"
    });

    const handleStart = () => {
        onStartIngestion(config);
    };

    return (
        <div className="flex flex-col gap-6 max-w-2xl mx-auto mt-10 text-gray-900 dark:text-gray-100 pb-20">
            <div className="text-center">
                <h2 className="text-2xl font-bold">
                    {t("ingestion.step4.title", "Final Configuration")}
                </h2>
                <p className="text-gray-500 dark:text-gray-400 mt-2">
                    {t("ingestion.step4.subtitle", "Configure processing settings and start ingestion.")}
                </p>
            </div>

            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm">
                <div className="flex items-center gap-2 mb-6 text-primary-600 dark:text-primary-400">
                    <Settings size={20} />
                    <h3 className="font-semibold">{t("ingestion.processingSettings", "Processing Settings")}</h3>
                </div>

                <div className="space-y-6">
                    {/* Chunking */}
                    <div>
                        <label className="block text-sm font-medium mb-1">
                            Chunk Size (tokens)
                        </label>
                        <input
                            type="number"
                            value={config.chunkSize}
                            onChange={(e) => setConfig({ ...config, chunkSize: Number(e.target.value) })}
                            className="w-full px-3 py-2 border rounded-md dark:bg-gray-900 dark:border-gray-600"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium mb-1">
                            Chunk Overlap (tokens)
                        </label>
                        <input
                            type="number"
                            value={config.chunkOverlap}
                            onChange={(e) => setConfig({ ...config, chunkOverlap: Number(e.target.value) })}
                            className="w-full px-3 py-2 border rounded-md dark:bg-gray-900 dark:border-gray-600"
                        />
                    </div>

                    {/* OCR */}
                    <div className="flex items-center justify-between py-2">
                        <div>
                            <label htmlFor="ocr-toggle" className="font-medium cursor-pointer">
                                {t("ingestion.enableOcr", "Enable OCR")}
                            </label>
                            <p className="text-xs text-gray-500">For scanned PDFs and images</p>
                        </div>
                        <input
                            id="ocr-toggle"
                            type="checkbox"
                            checked={config.useOcr}
                            onChange={(e) => setConfig({ ...config, useOcr: e.target.checked })}
                            className="w-5 h-5 text-primary-600 rounded"
                        />
                    </div>

                    {config.useOcr && (
                        <div>
                            <label className="block text-sm font-medium mb-1">
                                OCR Language
                            </label>
                            <input
                                type="text"
                                value={config.ocrLanguage}
                                onChange={(e) => setConfig({ ...config, ocrLanguage: e.target.value })}
                                className="w-full px-3 py-2 border rounded-md dark:bg-gray-900 dark:border-gray-600"
                                placeholder="e.g. eng+fra"
                            />
                        </div>
                    )}
                </div>
            </div>

            <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg flex items-start gap-3">
                <div className="mt-1 text-blue-600 dark:text-blue-400">ℹ️</div>
                <div>
                    <h4 className="font-medium text-blue-900 dark:text-blue-300">Ready to ingest</h4>
                    <p className="text-sm text-blue-800 dark:text-blue-200">
                        You are confusing to ingest <strong>{filesCount}</strong> files.
                        This process might take some time depending on document size and OCR settings.
                    </p>
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
                    onClick={handleStart}
                    className="flex items-center gap-2 px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md font-medium transition-colors shadow-sm"
                >
                    <Play size={18} />
                    {t("ingestion.startIngestion", "Start Ingestion")}
                </button>
            </div>
        </div>
    );
}
