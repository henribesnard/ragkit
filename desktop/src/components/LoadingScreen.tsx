import { Loader2 } from "lucide-react";
import { useTranslation } from "react-i18next";

interface LoadingScreenProps {
  message?: string;
}

export function LoadingScreen({ message }: LoadingScreenProps) {
  const { t } = useTranslation();
  const displayMessage = message || t("common.status.loading");
  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-50 dark:bg-gray-900">
      <div className="flex flex-col items-center space-y-4">
        <div className="relative">
          <div className="w-16 h-16 rounded-full bg-primary-100 dark:bg-primary-900/30" />
          <Loader2 className="absolute inset-0 w-16 h-16 text-primary-600 dark:text-primary-400 animate-spin" />
        </div>
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            RAGKIT Desktop
          </h2>
          <p className="mt-2 text-gray-600 dark:text-gray-400">{displayMessage}</p>
        </div>
      </div>
    </div>
  );
}
