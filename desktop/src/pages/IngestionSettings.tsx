// desktop/src/pages/IngestionSettings.tsx
import React, { useState } from 'react';
import { invoke } from '@tauri-apps/api/core';

interface IngestionConfig {
    ocr_enabled: boolean;
    ocr_language: string;
    lowercase: boolean;
    remove_urls: boolean;
    remove_punctuation: boolean;
}

interface PreviewResult {
    raw_content: string;
    cleaned_content: string;
    metadata: any;
    preview_success: boolean;
}

const IngestionSettings: React.FC = () => {
    const [config, setConfig] = useState<IngestionConfig>({
        ocr_enabled: false,
        ocr_language: 'eng',
        lowercase: false,
        remove_urls: false,
        remove_punctuation: false
    });

    const [filePath, setFilePath] = useState("");
    const [previewData, setPreviewData] = useState<PreviewResult | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleToggle = (key: keyof IngestionConfig) => {
        setConfig(prev => ({ ...prev, [key]: !prev[key] }));
    };

    const handlePreview = async () => {
        if (!filePath) {
            setError("Please enter a file path");
            return;
        }
        setError(null);
        try {
            setLoading(true);
            const result = await invoke('preview_ingestion', {
                file_path: filePath,
                config
            }) as PreviewResult;

            setPreviewData(result);
            setLoading(false);

        } catch (error) {
            console.error(error);
            setError(String(error));
            setLoading(false);
        }
    };

    return (
        <div className="p-6 h-full flex flex-col gap-6">
            <h1 className="text-2xl font-bold">Ingestion Settings</h1>

            <div className="grid grid-cols-2 gap-8 h-full">
                {/* Configuration Panel */}
                <div className="flex flex-col gap-4 border p-4 rounded-lg">
                    <h2 className="text-xl font-semibold">Configuration</h2>

                    <div className="flex flex-col gap-2 mb-4">
                        <label className="text-sm font-medium">Test File Path</label>
                        <input
                            type="text"
                            value={filePath}
                            onChange={(e) => setFilePath(e.target.value)}
                            placeholder="C:\path\to\document.pdf"
                            className="border p-2 rounded w-full"
                        />
                    </div>

                    <div className="flex items-center justify-between">
                        <label>OCR Enabled</label>
                        <input type="checkbox" checked={config.ocr_enabled} onChange={() => handleToggle('ocr_enabled')} />
                    </div>

                    <div className="flex items-center justify-between">
                        <label>Lowercase</label>
                        <input type="checkbox" checked={config.lowercase} onChange={() => handleToggle('lowercase')} />
                    </div>

                    <div className="flex items-center justify-between">
                        <label>Remove URLs</label>
                        <input type="checkbox" checked={config.remove_urls} onChange={() => handleToggle('remove_urls')} />
                    </div>

                    <div className="flex items-center justify-between">
                        <label>Remove Punctuation</label>
                        <input type="checkbox" checked={config.remove_punctuation} onChange={() => handleToggle('remove_punctuation')} />
                    </div>

                    {error && <div className="text-red-500 text-sm">{error}</div>}

                    <button
                        onClick={handlePreview}
                        className="mt-4 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:bg-gray-400"
                        disabled={loading}
                    >
                        {loading ? 'Processing...' : 'Test Ingestion Preview'}
                    </button>
                </div>

                {/* Preview Panel */}
                <div className="flex flex-col gap-4 border p-4 rounded-lg h-full overflow-hidden">
                    <h2 className="text-xl font-semibold">Preview</h2>

                    {previewData ? (
                        <div className="flex flex-col gap-4 h-full overflow-auto">
                            <div className="bg-gray-100 p-2 rounded">
                                <h3 className="font-bold text-sm text-gray-500">Metadata</h3>
                                <pre className="text-xs overflow-auto">{JSON.stringify(previewData.metadata, null, 2)}</pre>
                            </div>

                            <div className="grid grid-cols-2 gap-2 h-64">
                                <div className="border p-2 rounded overflow-auto">
                                    <h3 className="font-bold text-sm text-gray-500 mb-2">Raw Text</h3>
                                    <div className="text-xs whitespace-pre-wrap">{previewData.raw_content}</div>
                                </div>
                                <div className="border p-2 rounded bg-green-50 overflow-auto">
                                    <h3 className="font-bold text-sm text-gray-500 mb-2">Cleaned Text</h3>
                                    <div className="text-xs whitespace-pre-wrap">{previewData.cleaned_content}</div>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="text-gray-400 flex items-center justify-center h-full">
                            No preview available. Upload a file to test.
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default IngestionSettings;
