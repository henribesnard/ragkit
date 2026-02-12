/**
 * React hook for retry logic with state management.
 */

import { useState, useCallback, useRef } from "react";
import {
  withRetry,
  createRetryState,
  formatRetryMessage,
  type RetryConfig,
  type RetryState,
} from "../lib/retry";

export interface UseRetryOptions extends Partial<RetryConfig> {
  onSuccess?: () => void;
  onError?: (error: unknown) => void;
}

export interface UseRetryResult<T> {
  execute: () => Promise<T | undefined>;
  state: RetryState;
  retryMessage: string | null;
  reset: () => void;
  isLoading: boolean;
}

/**
 * Hook for executing async functions with retry logic.
 *
 * @example
 * ```tsx
 * const { execute, state, retryMessage, isLoading } = useRetry(
 *   () => fetchData(),
 *   { maxAttempts: 3, onError: (e) => console.error(e) }
 * );
 *
 * return (
 *   <div>
 *     <button onClick={execute} disabled={isLoading}>
 *       {isLoading ? 'Loading...' : 'Fetch'}
 *     </button>
 *     {retryMessage && <p>{retryMessage}</p>}
 *   </div>
 * );
 * ```
 */
export function useRetry<T>(
  fn: () => Promise<T>,
  options: UseRetryOptions = {}
): UseRetryResult<T> {
  const { onSuccess, onError, ...retryConfig } = options;
  const [state, setState] = useState<RetryState>(createRetryState);
  const [isLoading, setIsLoading] = useState(false);
  const abortRef = useRef(false);

  const execute = useCallback(async (): Promise<T | undefined> => {
    abortRef.current = false;
    setIsLoading(true);
    setState((prev) => ({ ...prev, isRetrying: false, error: null }));

    try {
      const result = await withRetry(fn, retryConfig, {
        onRetryStart: (attempt, delayMs) => {
          if (abortRef.current) return;
          setState((prev) => ({
            ...prev,
            isRetrying: true,
            attempt,
            nextRetryMs: delayMs,
          }));
        },
        onRetryComplete: () => {
          if (abortRef.current) return;
          setState((prev) => ({
            ...prev,
            isRetrying: false,
            attempt: 0,
            nextRetryMs: null,
          }));
        },
        onRetryFailed: (error) => {
          if (abortRef.current) return;
          setState((prev) => ({
            ...prev,
            isRetrying: false,
            error,
            nextRetryMs: null,
          }));
        },
      });

      if (!abortRef.current) {
        onSuccess?.();
      }
      return result;
    } catch (error) {
      if (!abortRef.current) {
        onError?.(error);
      }
      return undefined;
    } finally {
      if (!abortRef.current) {
        setIsLoading(false);
      }
    }
  }, [fn, retryConfig, onSuccess, onError]);

  const reset = useCallback(() => {
    abortRef.current = true;
    setIsLoading(false);
    setState(createRetryState());
  }, []);

  return {
    execute,
    state,
    retryMessage: formatRetryMessage(state),
    reset,
    isLoading,
  };
}

/**
 * Hook for lazy retry - only retries when manually triggered.
 *
 * @example
 * ```tsx
 * const { execute, retry, state, canRetry } = useLazyRetry(
 *   () => submitForm(data),
 *   { maxAttempts: 3 }
 * );
 *
 * return (
 *   <div>
 *     <button onClick={execute}>Submit</button>
 *     {state.error && canRetry && (
 *       <button onClick={retry}>Retry</button>
 *     )}
 *   </div>
 * );
 * ```
 */
export function useLazyRetry<T>(
  fn: () => Promise<T>,
  options: UseRetryOptions = {}
): UseRetryResult<T> & { canRetry: boolean } {
  const result = useRetry(fn, options);

  const canRetry =
    result.state.error !== null &&
    result.state.attempt < (options.maxAttempts ?? 3);

  return {
    ...result,
    canRetry,
  };
}

export default useRetry;
