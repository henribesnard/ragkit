import { AlertCircle, RefreshCw } from "lucide-react";

interface ErrorScreenProps {
  title: string;
  message: string;
  onRetry?: () => void;
}

export function ErrorScreen({ title, message, onRetry }: ErrorScreenProps) {
  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-50 dark:bg-gray-900 p-8">
      <div className="flex flex-col items-center max-w-md text-center space-y-4">
        <div className="w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
          <AlertCircle className="w-8 h-8 text-red-600 dark:text-red-400" />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            {title}
          </h2>
          <p className="mt-2 text-gray-600 dark:text-gray-400">{message}</p>
        </div>
        {onRetry && (
          <button
            onClick={onRetry}
            className="inline-flex items-center px-4 py-2 rounded-lg bg-primary-600 text-white hover:bg-primary-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Retry
          </button>
        )}
      </div>
    </div>
  );
}
