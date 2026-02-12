import { useState, useEffect, useCallback, useRef } from "react";
import { ipc } from "../lib/ipc";

type BackendStatus = "connecting" | "connected" | "error";

const MAX_WAIT_MS = 60000;
const RETRY_DELAY_MS = 1000;

export function useBackendStatus() {
  const [status, setStatus] = useState<BackendStatus>("connecting");
  const [error, setError] = useState<string | null>(null);
  const attemptRef = useRef(0);

  const checkHealth = useCallback(async () => {
    const attempt = ++attemptRef.current;
    const start = Date.now();
    let lastError: string | null = null;

    setStatus("connecting");
    setError(null);

    while (attemptRef.current === attempt) {
      try {
        const result = await ipc.healthCheck();

        if (result.ok) {
          setStatus("connected");
          return;
        }

        lastError = result.error || "Backend health check failed";
      } catch (err) {
        lastError = err instanceof Error ? err.message : "Unknown error";
      }

      if (Date.now() - start >= MAX_WAIT_MS) {
        setStatus("error");
        setError(lastError);
        return;
      }

      await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY_MS));
    }
  }, []);

  useEffect(() => {
    checkHealth();
  }, [checkHealth]);

  useEffect(() => {
    return () => {
      attemptRef.current += 1;
    };
  }, []);

  return {
    status,
    error,
    retry: checkHealth,
  };
}
