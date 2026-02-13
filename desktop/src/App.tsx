import { useEffect, useState, Suspense, lazy } from "react";
import { useTranslation } from "react-i18next";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Layout } from "./components/Layout";
import { useBackendStatus } from "./hooks/useBackendStatus";
import { LoadingScreen } from "./components/LoadingScreen";
import { ErrorScreen } from "./components/ErrorScreen";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { ToastProvider, ConfirmProvider } from "./components/ui";

// Lazy load pages for better initial load time
const Chat = lazy(() => import("./pages/Chat").then((m) => ({ default: m.Chat })));
const KnowledgeBases = lazy(() =>
  import("./pages/KnowledgeBases").then((m) => ({ default: m.KnowledgeBases }))
);
const Settings = lazy(() =>
  import("./pages/Settings").then((m) => ({ default: m.Settings }))
);
const Logs = lazy(() => import("./pages/Logs"));
const IngestionWizard = lazy(() =>
  import("./pages/IngestionWizard").then((m) => ({ default: m.IngestionWizard }))
);

// Page loading fallback
function PageLoader() {
  const { t } = useTranslation();
  return (
    <div className="flex items-center justify-center h-full">
      <div className="flex flex-col items-center gap-3">
        <div className="w-8 h-8 border-2 border-primary-600 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {t("common.status.loading")}
        </p>
      </div>
    </div>
  );
}

function App() {
  const { t } = useTranslation();
  const { status, error, retry } = useBackendStatus();
  const [darkMode, setDarkMode] = useState(() => {
    if (typeof window !== "undefined") {
      return window.matchMedia("(prefers-color-scheme: dark)").matches;
    }
    return false;
  });

  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
  }, [darkMode]);

  // Show loading while backend is starting
  if (status === "connecting") {
    return <LoadingScreen message={t("app.backendStarting")} />;
  }

  // Show error if backend failed to start
  if (status === "error") {
    return (
      <ErrorScreen
        title={t("app.backendErrorTitle")}
        message={error || t("app.backendErrorMessage")}
        onRetry={retry}
      />
    );
  }

  return (
    <ErrorBoundary>
      <ToastProvider position="bottom-right">
        <ConfirmProvider>
          <BrowserRouter>
            <Layout darkMode={darkMode} onToggleDarkMode={() => setDarkMode(!darkMode)}>
              <Suspense fallback={<PageLoader />}>
                <Routes>
                  <Route path="/" element={<Navigate to="/ingestion" replace />} />
                  {/* <Route path="/chat" element={<Chat />} /> */}
                  {/* <Route path="/chat/:conversationId" element={<Chat />} /> */}
                  {/* <Route path="/knowledge-bases" element={<KnowledgeBases />} /> */}
                  {/* <Route path="/settings" element={<Settings />} /> */}
                  <Route path="/ingestion" element={<IngestionWizard />} />
                  <Route path="/logs" element={<Logs />} />
                </Routes>
              </Suspense>
            </Layout>
          </BrowserRouter>
        </ConfirmProvider>
      </ToastProvider>
    </ErrorBoundary>
  );
}

export default App;
