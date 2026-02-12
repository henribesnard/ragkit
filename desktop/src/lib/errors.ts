/**
 * User-friendly error messages mapping.
 *
 * Maps technical error messages to human-readable messages.
 */

// Error categories
export type ErrorCategory =
  | "network"
  | "backend"
  | "ollama"
  | "api_key"
  | "file"
  | "knowledge_base"
  | "chat"
  | "unknown";

// Error info structure
export interface ErrorInfo {
  title: string;
  message: string;
  category: ErrorCategory;
  recoverable: boolean;
  suggestion?: string;
}

// Error patterns to match against
interface ErrorPattern {
  pattern: RegExp | string;
  info: ErrorInfo;
}

// Define error patterns
const ERROR_PATTERNS: ErrorPattern[] = [
  // Network errors
  {
    pattern: /fetch failed|network error|failed to fetch/i,
    info: {
      title: "Connection Error",
      message: "Unable to connect to the server.",
      category: "network",
      recoverable: true,
      suggestion: "Check your internet connection and try again.",
    },
  },
  {
    pattern: /ECONNREFUSED|connection refused/i,
    info: {
      title: "Server Unavailable",
      message: "The backend server is not responding.",
      category: "backend",
      recoverable: true,
      suggestion: "The server may be starting up. Please wait a moment and try again.",
    },
  },
  {
    pattern: /timeout|timed out|ETIMEDOUT/i,
    info: {
      title: "Request Timeout",
      message: "The request took too long to complete.",
      category: "network",
      recoverable: true,
      suggestion: "Try again. If the problem persists, the server may be overloaded.",
    },
  },

  // Backend errors
  {
    pattern: /backend.*not.*ready|backend.*starting/i,
    info: {
      title: "Starting Up",
      message: "The application is still starting up.",
      category: "backend",
      recoverable: true,
      suggestion: "Please wait a few seconds and try again.",
    },
  },
  {
    pattern: /internal server error|500/i,
    info: {
      title: "Server Error",
      message: "Something went wrong on the server.",
      category: "backend",
      recoverable: true,
      suggestion: "Try again. If the problem persists, restart the application.",
    },
  },

  // Ollama errors
  {
    pattern: /ollama.*not.*installed/i,
    info: {
      title: "Ollama Not Installed",
      message: "Ollama is required for local AI processing but is not installed.",
      category: "ollama",
      recoverable: false,
      suggestion: "Install Ollama from ollama.ai to use local AI models.",
    },
  },
  {
    pattern: /ollama.*not.*running/i,
    info: {
      title: "Ollama Not Running",
      message: "Ollama is installed but not currently running.",
      category: "ollama",
      recoverable: true,
      suggestion: "Start the Ollama service from Settings or run 'ollama serve' in terminal.",
    },
  },
  {
    pattern: /model.*not.*found|no.*model/i,
    info: {
      title: "Model Not Found",
      message: "The requested AI model is not available.",
      category: "ollama",
      recoverable: true,
      suggestion: "Download the model from Settings or choose a different model.",
    },
  },
  {
    pattern: /pull.*failed|download.*failed/i,
    info: {
      title: "Download Failed",
      message: "Failed to download the AI model.",
      category: "ollama",
      recoverable: true,
      suggestion: "Check your internet connection and try again.",
    },
  },

  // API Key errors
  {
    pattern: /invalid.*api.*key|api.*key.*invalid|unauthorized|401/i,
    info: {
      title: "Invalid API Key",
      message: "The API key provided is not valid.",
      category: "api_key",
      recoverable: true,
      suggestion: "Check your API key in Settings and make sure it's correct.",
    },
  },
  {
    pattern: /api.*key.*required|missing.*api.*key/i,
    info: {
      title: "API Key Required",
      message: "An API key is required to use this service.",
      category: "api_key",
      recoverable: true,
      suggestion: "Add your API key in Settings.",
    },
  },
  {
    pattern: /rate.*limit|too.*many.*requests|429/i,
    info: {
      title: "Rate Limited",
      message: "Too many requests. You've hit the API rate limit.",
      category: "api_key",
      recoverable: true,
      suggestion: "Wait a moment before trying again.",
    },
  },
  {
    pattern: /quota.*exceeded|insufficient.*quota/i,
    info: {
      title: "Quota Exceeded",
      message: "You've exceeded your API usage quota.",
      category: "api_key",
      recoverable: false,
      suggestion: "Check your API account for billing or upgrade your plan.",
    },
  },

  // File errors
  {
    pattern: /file.*not.*found|ENOENT/i,
    info: {
      title: "File Not Found",
      message: "The requested file could not be found.",
      category: "file",
      recoverable: false,
      suggestion: "Make sure the file exists and the path is correct.",
    },
  },
  {
    pattern: /permission.*denied|EACCES/i,
    info: {
      title: "Permission Denied",
      message: "You don't have permission to access this file.",
      category: "file",
      recoverable: false,
      suggestion: "Check file permissions or choose a different location.",
    },
  },
  {
    pattern: /unsupported.*file.*type|invalid.*file.*format/i,
    info: {
      title: "Unsupported File",
      message: "This file type is not supported.",
      category: "file",
      recoverable: false,
      suggestion: "Supported formats: PDF, TXT, MD, DOCX.",
    },
  },

  // Knowledge Base errors
  {
    pattern: /knowledge.*base.*not.*found/i,
    info: {
      title: "Knowledge Base Not Found",
      message: "The knowledge base could not be found.",
      category: "knowledge_base",
      recoverable: false,
      suggestion: "The knowledge base may have been deleted. Create a new one.",
    },
  },
  {
    pattern: /no.*documents|empty.*knowledge.*base/i,
    info: {
      title: "No Documents",
      message: "The knowledge base has no documents.",
      category: "knowledge_base",
      recoverable: true,
      suggestion: "Add some documents to start asking questions.",
    },
  },
  {
    pattern: /embedding.*failed|vector.*error/i,
    info: {
      title: "Indexing Error",
      message: "Failed to process documents for search.",
      category: "knowledge_base",
      recoverable: true,
      suggestion: "Try adding the documents again.",
    },
  },

  // Chat errors
  {
    pattern: /generation.*failed|llm.*error/i,
    info: {
      title: "Response Generation Failed",
      message: "Failed to generate a response.",
      category: "chat",
      recoverable: true,
      suggestion: "Try asking your question again.",
    },
  },
  {
    pattern: /context.*too.*long|token.*limit/i,
    info: {
      title: "Context Too Long",
      message: "The conversation is too long for the AI to process.",
      category: "chat",
      recoverable: true,
      suggestion: "Start a new conversation to continue.",
    },
  },
];

// Default error for unknown errors
const DEFAULT_ERROR: ErrorInfo = {
  title: "Something Went Wrong",
  message: "An unexpected error occurred.",
  category: "unknown",
  recoverable: true,
  suggestion: "Try again. If the problem persists, restart the application.",
};

/**
 * Parse an error and return user-friendly error info.
 */
export function parseError(error: unknown): ErrorInfo {
  const errorString = errorToString(error);

  for (const { pattern, info } of ERROR_PATTERNS) {
    if (typeof pattern === "string") {
      if (errorString.toLowerCase().includes(pattern.toLowerCase())) {
        return info;
      }
    } else if (pattern.test(errorString)) {
      return info;
    }
  }

  return {
    ...DEFAULT_ERROR,
    message: truncateMessage(errorString),
  };
}

/**
 * Convert any error to a string.
 */
function errorToString(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  if (typeof error === "string") {
    return error;
  }
  if (error && typeof error === "object") {
    if ("message" in error && typeof error.message === "string") {
      return error.message;
    }
    if ("error" in error && typeof error.error === "string") {
      return error.error;
    }
    return JSON.stringify(error);
  }
  return String(error);
}

/**
 * Truncate long error messages.
 */
function truncateMessage(message: string, maxLength = 100): string {
  if (message.length <= maxLength) {
    return message;
  }
  return message.slice(0, maxLength - 3) + "...";
}

/**
 * Check if an error is recoverable (can be retried).
 */
export function isRecoverableError(error: unknown): boolean {
  return parseError(error).recoverable;
}

/**
 * Get the error category.
 */
export function getErrorCategory(error: unknown): ErrorCategory {
  return parseError(error).category;
}

/**
 * Format error for display.
 */
export function formatErrorForDisplay(error: unknown): {
  title: string;
  message: string;
  suggestion?: string;
} {
  const info = parseError(error);
  return {
    title: info.title,
    message: info.message,
    suggestion: info.suggestion,
  };
}
