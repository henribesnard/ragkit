/**
 * IPC client for communicating with the Python backend.
 *
 * Uses Tauri's invoke API to call Rust commands which proxy to Python.
 */

import { invoke } from "@tauri-apps/api/core";

// Response types
interface HealthCheckResponse {
  ok: boolean;
  version?: string;
  error?: string;
}

interface QueryResponse {
  answer: string;
  sources: Source[];
  latency_ms: number;
}

interface Source {
  filename: string;
  chunk: string;
  score: number;
}

interface KnowledgeBase {
  id: string;
  name: string;
  description: string | null;
  embedding_model: string;
  document_count: number;
  chunk_count: number;
  created_at: string;
  updated_at: string;
}

interface Conversation {
  id: string;
  kb_id: string | null;
  title: string | null;
  created_at: string;
  updated_at: string;
}

interface Message {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  sources?: Source[];
  latency_ms?: number;
  created_at: string;
}

interface Settings {
  embedding_provider: string;
  embedding_model: string;
  llm_provider: string;
  llm_model: string;
  theme: "light" | "dark" | "system";
}

// Ollama types
interface OllamaStatus {
  installed: boolean;
  running: boolean;
  version: string | null;
  error: string | null;
}

interface OllamaModel {
  name: string;
  size: number;
  size_formatted: string;
  digest: string;
  modified_at: string;
}

interface RecommendedModel {
  name: string;
  size: string;
  description: string;
  quality: "good" | "excellent";
  speed: "fast" | "medium" | "very_fast";
}

interface EmbeddingModel {
  name: string;
  size: string;
  dimensions: number;
  description: string;
}

interface InstallInstructions {
  platform: string;
  instructions: string;
  all_platforms: Record<string, string>;
}

// IPC Client
export const ipc = {
  // Health & Status
  async healthCheck(): Promise<HealthCheckResponse> {
    try {
      return await invoke<HealthCheckResponse>("health_check");
    } catch (error) {
      return { ok: false, error: String(error) };
    }
  },

  // Knowledge Bases
  async listKnowledgeBases(): Promise<KnowledgeBase[]> {
    return invoke<KnowledgeBase[]>("list_knowledge_bases");
  },

  async createKnowledgeBase(params: {
    name: string;
    description?: string;
    embedding_model?: string;
  }): Promise<KnowledgeBase> {
    return invoke<KnowledgeBase>("create_knowledge_base", { params });
  },

  async deleteKnowledgeBase(kbId: string): Promise<boolean> {
    return invoke<boolean>("delete_knowledge_base", { kbId });
  },

  async addDocuments(kbId: string, paths: string[]): Promise<void> {
    return invoke("add_documents", { kbId, paths });
  },

  // Conversations
  async listConversations(kbId?: string): Promise<Conversation[]> {
    return invoke<Conversation[]>("list_conversations", { kbId });
  },

  async createConversation(kbId?: string): Promise<Conversation> {
    return invoke<Conversation>("create_conversation", { kbId });
  },

  async deleteConversation(convId: string): Promise<boolean> {
    return invoke<boolean>("delete_conversation", { convId });
  },

  async getMessages(convId: string): Promise<Message[]> {
    return invoke<Message[]>("get_messages", { convId });
  },

  // Chat
  async query(params: {
    kbId: string;
    conversationId: string;
    question: string;
  }): Promise<QueryResponse> {
    return invoke<QueryResponse>("query", { params });
  },

  // Settings
  async getSettings(): Promise<Settings> {
    return invoke<Settings>("get_settings");
  },

  async updateSettings(settings: Partial<Settings>): Promise<Settings> {
    return invoke<Settings>("update_settings", { settings });
  },

  // API Keys
  async setApiKey(provider: string, apiKey: string): Promise<void> {
    return invoke("set_api_key", { provider, apiKey });
  },

  async hasApiKey(provider: string): Promise<boolean> {
    return invoke<boolean>("has_api_key", { provider });
  },

  async deleteApiKey(provider: string): Promise<boolean> {
    return invoke<boolean>("delete_api_key", { provider });
  },

  // File dialogs (via Tauri)
  async selectFiles(filters?: { name: string; extensions: string[] }[]): Promise<string[] | null> {
    const { open } = await import("@tauri-apps/plugin-dialog");
    const result = await open({
      multiple: true,
      filters: filters || [
        { name: "Documents", extensions: ["pdf", "txt", "md", "docx"] },
      ],
    });
    return result as string[] | null;
  },

  async selectFolder(): Promise<string | null> {
    const { open } = await import("@tauri-apps/plugin-dialog");
    return open({ directory: true }) as Promise<string | null>;
  },

  // Ollama
  async getOllamaStatus(): Promise<OllamaStatus> {
    return invoke<OllamaStatus>("get_ollama_status");
  },

  async listOllamaModels(): Promise<OllamaModel[]> {
    return invoke<OllamaModel[]>("list_ollama_models");
  },

  async getRecommendedModels(): Promise<Record<string, RecommendedModel>> {
    return invoke<Record<string, RecommendedModel>>("get_recommended_models");
  },

  async getOllamaEmbeddingModels(): Promise<Record<string, EmbeddingModel>> {
    return invoke<Record<string, EmbeddingModel>>("get_ollama_embedding_models");
  },

  async pullOllamaModel(modelName: string): Promise<void> {
    return invoke("pull_ollama_model", { modelName });
  },

  async deleteOllamaModel(modelName: string): Promise<void> {
    return invoke("delete_ollama_model", { modelName });
  },

  async startOllamaService(): Promise<void> {
    return invoke("start_ollama_service");
  },

  async getInstallInstructions(): Promise<InstallInstructions> {
    return invoke<InstallInstructions>("get_install_instructions");
  },
};

// Export types
export type {
  HealthCheckResponse,
  QueryResponse,
  Source,
  KnowledgeBase,
  Conversation,
  Message,
  Settings,
  OllamaStatus,
  OllamaModel,
  RecommendedModel,
  EmbeddingModel,
  InstallInstructions,
};
