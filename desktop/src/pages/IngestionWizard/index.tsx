import { useState } from "react";
import { Step1_SourceSelection } from "./Step1_SourceSelection";
import { Step2_Analysis } from "./Step2_Analysis";
import { Step3_MetadataReview } from "./Step3_MetadataReview";
import { Step4_Configuration, IngestionConfig } from "./Step4_Configuration";
import { ipc, ScanDirectoryResponse } from "../../lib/ipc";
import { LoadingScreen } from "../../components/LoadingScreen";
import { useTranslation } from "react-i18next";

export function IngestionWizard() {
    const { t } = useTranslation();
    const [step, setStep] = useState(1);
    const [isLoading, setIsLoading] = useState(false);

    // State
    const [sourcePath, setSourcePath] = useState("");
    const [recursive, setRecursive] = useState(true);
    const [scanResult, setScanResult] = useState<ScanDirectoryResponse | null>(null);
    const [selectedFileTypes, setSelectedFileTypes] = useState<string[]>([]);
    const [filesMetadata, setFilesMetadata] = useState<any[]>([]);

    const handleStep1Next = async (path: string, isRecursive: boolean) => {
        setSourcePath(path);
        setRecursive(isRecursive);
        setIsLoading(true);

        try {
            const result = await ipc.scanDirectory(path, isRecursive);
            setScanResult(result);
            setStep(2);
        } catch (error) {
            console.error("Scan failed:", error);
            // TODO: Show error toast
        } finally {
            setIsLoading(false);
        }
    };

    const handleStep2Next = (types: string[]) => {
        setSelectedFileTypes(types);
        setStep(3);
    };

    const handleStep2Back = () => {
        setStep(1);
        setScanResult(null);
    };

    const handleStep3Next = (files: any[]) => {
        console.log("Files with metadata:", files);
        setFilesMetadata(files);
        setStep(4);
    };

    const handleStep3Back = () => {
        setStep(2);
    };

    const handleStartIngestion = async (config: IngestionConfig) => {
        setIsLoading(true);
        try {
            // TODO: Call backend to start ingestion
            console.log("Starting ingestion with config:", config);
            console.log("Files:", filesMetadata);

            // Simulate backend call
            await new Promise(r => setTimeout(r, 2000));
            alert("Ingestion started! (This is a simulation)");

            // Reset or redirect
            // setStep(1);
        } catch (error) {
            console.error("Ingestion failed:", error);
        } finally {
            setIsLoading(false);
        }
    };

    if (isLoading) {
        return <LoadingScreen message={t("ingestion.scanning", "Scanning directory...")} />;
    }

    return (
        <div className="container mx-auto px-4 py-8 h-full">
            {/* Progress Bar */}
            <div className="max-w-2xl mx-auto mb-8">
                <div className="flex items-center justify-between text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
                    <span className={step >= 1 ? "text-primary-600 dark:text-primary-400" : ""}>Select Source</span>
                    <span className={step >= 2 ? "text-primary-600 dark:text-primary-400" : ""}>Analysis</span>
                    <span className={step >= 3 ? "text-primary-600 dark:text-primary-400" : ""}>Metadata</span>
                    <span className={step >= 4 ? "text-primary-600 dark:text-primary-400" : ""}>Configure</span>
                </div>
                <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div
                        className="h-full bg-primary-600 transition-all duration-300 ease-out"
                        style={{ width: `${(step / 4) * 100}%` }}
                    />
                </div>
            </div>

            {/* Steps */}
            {step === 1 && (
                <Step1_SourceSelection
                    onNext={handleStep1Next}
                    initialPath={sourcePath}
                    initialRecursive={recursive}
                />
            )}

            {step === 2 && scanResult && (
                <Step2_Analysis
                    scanResult={scanResult}
                    onNext={handleStep2Next}
                    onBack={handleStep2Back}
                    initialSelectedTypes={selectedFileTypes.length > 0 ? selectedFileTypes : undefined}
                />
            )}

            {step === 3 && (
                <Step3_MetadataReview
                    selectedTypes={selectedFileTypes}
                    sourcePath={sourcePath}
                    recursive={recursive}
                    onNext={handleStep3Next}
                    onBack={handleStep3Back}
                />
            )}

            {step === 4 && (
                <Step4_Configuration
                    filesCount={filesMetadata.length}
                    onBack={handleStep3Back}
                    onStartIngestion={handleStartIngestion}
                />
            )}
        </div>
    );
}
