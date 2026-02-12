/**
 * Retry logic with exponential backoff and UI feedback.
 */

import { isRecoverableError } from "./errors";

// Retry configuration
export interface RetryConfig {
  maxAttempts: number;
  initialDelayMs: number;
  maxDelayMs: number;
  backoffMultiplier: number;
  shouldRetry?: (error: unknown, attempt: number) => boolean;
}

// Retry state for UI feedback
export interface RetryState {
  isRetrying: boolean;
  attempt: number;
  maxAttempts: number;
  nextRetryMs: number | null;
  error: unknown | null;
}

// Retry callbacks for UI updates
export interface RetryCallbacks {
  onRetryStart?: (attempt: number, delayMs: number) => void;
  onRetryComplete?: () => void;
  onRetryFailed?: (error: unknown) => void;
}

// Default configuration
const DEFAULT_CONFIG: RetryConfig = {
  maxAttempts: 3,
  initialDelayMs: 1000,
  maxDelayMs: 10000,
  backoffMultiplier: 2,
  shouldRetry: (error) => isRecoverableError(error),
};

/**
 * Sleep for a specified duration.
 */
function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Calculate delay for a given attempt using exponential backoff.
 */
function calculateDelay(attempt: number, config: RetryConfig): number {
  const delay = config.initialDelayMs * Math.pow(config.backoffMultiplier, attempt - 1);
  // Add jitter (+/-10%)
  const jitter = delay * 0.1 * (Math.random() * 2 - 1);
  return Math.min(delay + jitter, config.maxDelayMs);
}

/**
 * Execute a function with retry logic.
 *
 * @param fn The async function to execute
 * @param config Retry configuration
 * @param callbacks Optional callbacks for UI feedback
 * @returns The result of the function
 * @throws The last error if all retries fail
 */
export async function withRetry<T>(
  fn: () => Promise<T>,
  config: Partial<RetryConfig> = {},
  callbacks?: RetryCallbacks
): Promise<T> {
  const finalConfig: RetryConfig = { ...DEFAULT_CONFIG, ...config };
  let lastError: unknown;

  for (let attempt = 1; attempt <= finalConfig.maxAttempts; attempt++) {
    try {
      const result = await fn();
      if (attempt > 1) {
        callbacks?.onRetryComplete?.();
      }
      return result;
    } catch (error) {
      lastError = error;

      // Check if we should retry
      const shouldRetry =
        attempt < finalConfig.maxAttempts &&
        (finalConfig.shouldRetry?.(error, attempt) ?? true);

      if (!shouldRetry) {
        callbacks?.onRetryFailed?.(error);
        throw error;
      }

      // Calculate delay and notify
      const delayMs = calculateDelay(attempt, finalConfig);
      callbacks?.onRetryStart?.(attempt, delayMs);

      // Wait before retrying
      await sleep(delayMs);
    }
  }

  // All retries failed
  callbacks?.onRetryFailed?.(lastError);
  throw lastError;
}

/**
 * Create a retry wrapper that maintains state for UI feedback.
 */
export function createRetryHandler<T>(
  fn: () => Promise<T>,
  config: Partial<RetryConfig> = {}
): {
  execute: () => Promise<T>;
  getState: () => RetryState;
  reset: () => void;
} {
  let state: RetryState = {
    isRetrying: false,
    attempt: 0,
    maxAttempts: config.maxAttempts ?? DEFAULT_CONFIG.maxAttempts,
    nextRetryMs: null,
    error: null,
  };

  const execute = async (): Promise<T> => {
    state = { ...state, isRetrying: true, error: null };

    try {
      return await withRetry(fn, config, {
        onRetryStart: (attempt, delayMs) => {
          state = {
            ...state,
            attempt,
            nextRetryMs: delayMs,
          };
        },
        onRetryComplete: () => {
          state = {
            ...state,
            isRetrying: false,
            attempt: 0,
            nextRetryMs: null,
          };
        },
        onRetryFailed: (error) => {
          state = {
            ...state,
            isRetrying: false,
            error,
            nextRetryMs: null,
          };
        },
      });
    } finally {
      state = { ...state, isRetrying: false };
    }
  };

  const getState = () => ({ ...state });

  const reset = () => {
    state = {
      isRetrying: false,
      attempt: 0,
      maxAttempts: config.maxAttempts ?? DEFAULT_CONFIG.maxAttempts,
      nextRetryMs: null,
      error: null,
    };
  };

  return { execute, getState, reset };
}

/**
 * React hook for retry logic with state management.
 * Usage: const { execute, state, reset } = useRetry(fetchData, { maxAttempts: 3 });
 */
export function createRetryState(): RetryState {
  return {
    isRetrying: false,
    attempt: 0,
    maxAttempts: DEFAULT_CONFIG.maxAttempts,
    nextRetryMs: null,
    error: null,
  };
}

/**
 * Helper to format retry state for display.
 */
export function formatRetryMessage(state: RetryState): string | null {
  if (!state.isRetrying) {
    return null;
  }

  if (state.nextRetryMs !== null) {
    const seconds = Math.ceil(state.nextRetryMs / 1000);
    return `Retrying in ${seconds}s (attempt ${state.attempt + 1}/${state.maxAttempts})...`;
  }

  return `Retrying (attempt ${state.attempt}/${state.maxAttempts})...`;
}

/**
 * Quick retry presets for common scenarios.
 */
export const RetryPresets = {
  // Quick retry for fast operations
  quick: {
    maxAttempts: 2,
    initialDelayMs: 500,
    maxDelayMs: 2000,
    backoffMultiplier: 2,
  } as Partial<RetryConfig>,

  // Standard retry for API calls
  standard: {
    maxAttempts: 3,
    initialDelayMs: 1000,
    maxDelayMs: 10000,
    backoffMultiplier: 2,
  } as Partial<RetryConfig>,

  // Aggressive retry for critical operations
  aggressive: {
    maxAttempts: 5,
    initialDelayMs: 500,
    maxDelayMs: 30000,
    backoffMultiplier: 2,
  } as Partial<RetryConfig>,

  // Patient retry for slow operations
  patient: {
    maxAttempts: 3,
    initialDelayMs: 2000,
    maxDelayMs: 30000,
    backoffMultiplier: 3,
  } as Partial<RetryConfig>,
};
