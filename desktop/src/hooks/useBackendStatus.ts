import { useState, useEffect, useCallback } from "react";
import { ipc } from "../lib/ipc";

type BackendStatus = "connecting" | "connected" | "error";

export function useBackendStatus() {
  const [status, setStatus] = useState<BackendStatus>("connecting");
  const [error, setError] = useState<string | null>(null);

  const checkHealth = useCallback(async () => {
    try {
      setStatus("connecting");
      setError(null);

      const result = await ipc.healthCheck();

      if (result.ok) {
        setStatus("connected");
      } else {
        setStatus("error");
        setError(result.error || "Backend health check failed");
      }
    } catch (err) {
      setStatus("error");
      setError(err instanceof Error ? err.message : "Unknown error");
    }
  }, []);

  useEffect(() => {
    checkHealth();
  }, [checkHealth]);

  return {
    status,
    error,
    retry: checkHealth,
  };
}
