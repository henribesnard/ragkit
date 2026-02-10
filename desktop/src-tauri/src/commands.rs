//! Tauri commands that proxy to the Python backend.

use crate::backend::backend_request;
use reqwest::Method;
use serde::{Deserialize, Serialize};
use serde_json::json;

// ============================================================================
// Response Types
// ============================================================================

#[derive(Debug, Serialize, Deserialize)]
pub struct HealthCheckResponse {
    pub ok: bool,
    pub version: Option<String>,
    pub error: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct KnowledgeBase {
    pub id: String,
    pub name: String,
    pub description: Option<String>,
    pub embedding_model: String,
    pub embedding_dimensions: i32,
    pub document_count: i32,
    pub chunk_count: i32,
    pub created_at: String,
    pub updated_at: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Conversation {
    pub id: String,
    pub kb_id: Option<String>,
    pub title: Option<String>,
    pub created_at: String,
    pub updated_at: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Message {
    pub id: String,
    pub conversation_id: String,
    pub role: String,
    pub content: String,
    pub sources: Option<Vec<Source>>,
    pub latency_ms: Option<i32>,
    pub created_at: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Source {
    pub filename: String,
    pub chunk: String,
    pub score: f32,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct QueryResponse {
    pub answer: String,
    pub sources: Vec<Source>,
    pub latency_ms: i32,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct AddFolderFailure {
    pub path: String,
    pub error: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct AddFolderResponse {
    pub added: Vec<String>,
    pub failed: Vec<AddFolderFailure>,
    pub total_processed: usize,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Settings {
    pub embedding_provider: String,
    pub embedding_model: String,
    pub embedding_chunk_strategy: String,
    pub embedding_chunk_size: i32,
    pub embedding_chunk_overlap: i32,
    pub retrieval_architecture: String,
    pub retrieval_top_k: i32,
    pub retrieval_semantic_weight: f64,
    pub retrieval_lexical_weight: f64,
    pub retrieval_rerank_weight: f64,
    pub retrieval_rerank_enabled: bool,
    pub retrieval_rerank_provider: String,
    pub retrieval_max_chunks: i32,
    pub llm_provider: String,
    pub llm_model: String,
    pub theme: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct WizardProfileResponse {
    pub profile_name: String,
    pub description: String,
    pub config_summary: serde_json::Value,
    pub full_config: serde_json::Value,
}

// ============================================================================
// Request Types
// ============================================================================

#[derive(Debug, Serialize, Deserialize)]
pub struct CreateKnowledgeBaseParams {
    pub name: String,
    pub description: Option<String>,
    pub embedding_model: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct QueryParams {
    pub kb_id: String,
    pub conversation_id: String,
    pub question: String,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct AddFolderParams {
    pub kb_id: String,
    pub folder_path: String,
    pub recursive: bool,
    pub file_types: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct WizardAnswers {
    pub kb_type: String,
    pub has_tables_diagrams: bool,
    pub needs_multi_document: bool,
    pub large_documents: bool,
    pub needs_precision: bool,
    pub frequent_updates: bool,
    pub cite_page_numbers: bool,
}

// ============================================================================
// Commands
// ============================================================================

/// Health check command
#[tauri::command]
pub async fn health_check() -> Result<HealthCheckResponse, String> {
    match backend_request::<HealthCheckResponse>(Method::GET, "/health", None).await {
        Ok(resp) => Ok(resp),
        Err(e) => Ok(HealthCheckResponse {
            ok: false,
            version: None,
            error: Some(e.to_string()),
        }),
    }
}

/// List all knowledge bases
#[tauri::command]
pub async fn list_knowledge_bases() -> Result<Vec<KnowledgeBase>, String> {
    backend_request(Method::GET, "/api/knowledge-bases", None)
        .await
        .map_err(|e| e.to_string())
}

/// Create a new knowledge base
#[tauri::command]
pub async fn create_knowledge_base(params: CreateKnowledgeBaseParams) -> Result<KnowledgeBase, String> {
    backend_request(
        Method::POST,
        "/api/knowledge-bases",
        Some(serde_json::to_value(&params).unwrap()),
    )
    .await
    .map_err(|e| e.to_string())
}

/// Delete a knowledge base
#[tauri::command]
pub async fn delete_knowledge_base(kb_id: String) -> Result<bool, String> {
    backend_request(
        Method::DELETE,
        &format!("/api/knowledge-bases/{}", kb_id),
        None,
    )
    .await
    .map_err(|e| e.to_string())
}

/// Add documents to a knowledge base
#[tauri::command]
pub async fn add_documents(kb_id: String, paths: Vec<String>) -> Result<(), String> {
    backend_request::<serde_json::Value>(
        Method::POST,
        &format!("/api/knowledge-bases/{}/documents", kb_id),
        Some(json!({ "paths": paths })),
    )
    .await
    .map(|_| ())
    .map_err(|e| e.to_string())
}

/// Add a folder to a knowledge base
#[tauri::command]
pub async fn add_folder(params: AddFolderParams) -> Result<AddFolderResponse, String> {
    backend_request(
        Method::POST,
        &format!("/api/knowledge-bases/{}/folders", params.kb_id),
        Some(json!({
            "folder_path": params.folder_path,
            "recursive": params.recursive,
            "file_types": params.file_types,
        })),
    )
    .await
    .map_err(|e| e.to_string())
}

/// List conversations
#[tauri::command]
pub async fn list_conversations(kb_id: Option<String>) -> Result<Vec<Conversation>, String> {
    let path = match kb_id {
        Some(id) => format!("/api/conversations?kb_id={}", id),
        None => "/api/conversations".to_string(),
    };
    backend_request(Method::GET, &path, None)
        .await
        .map_err(|e| e.to_string())
}

/// Create a new conversation
#[tauri::command]
pub async fn create_conversation(kb_id: Option<String>) -> Result<Conversation, String> {
    backend_request(
        Method::POST,
        "/api/conversations",
        Some(json!({ "kb_id": kb_id })),
    )
    .await
    .map_err(|e| e.to_string())
}

/// Delete a conversation
#[tauri::command]
pub async fn delete_conversation(conv_id: String) -> Result<bool, String> {
    backend_request(
        Method::DELETE,
        &format!("/api/conversations/{}", conv_id),
        None,
    )
    .await
    .map_err(|e| e.to_string())
}

/// Get messages in a conversation
#[tauri::command]
pub async fn get_messages(conv_id: String) -> Result<Vec<Message>, String> {
    backend_request(
        Method::GET,
        &format!("/api/conversations/{}/messages", conv_id),
        None,
    )
    .await
    .map_err(|e| e.to_string())
}

/// Query the knowledge base
#[tauri::command]
pub async fn query(params: QueryParams) -> Result<QueryResponse, String> {
    backend_request(
        Method::POST,
        "/api/query",
        Some(serde_json::to_value(&params).unwrap()),
    )
    .await
    .map_err(|e| e.to_string())
}

/// Get settings
#[tauri::command]
pub async fn get_settings() -> Result<Settings, String> {
    backend_request(Method::GET, "/api/settings", None)
        .await
        .map_err(|e| e.to_string())
}

/// Update settings
#[tauri::command]
pub async fn update_settings(settings: Settings) -> Result<Settings, String> {
    backend_request(
        Method::PUT,
        "/api/settings",
        Some(serde_json::to_value(&settings).unwrap()),
    )
    .await
    .map_err(|e| e.to_string())
}

// ============================================================================
// Wizard Commands
// ============================================================================

/// Analyze wizard answers and return a profile recommendation
#[tauri::command]
pub async fn analyze_wizard_profile(
    params: WizardAnswers,
) -> Result<WizardProfileResponse, String> {
    backend_request(
        Method::POST,
        "/api/wizard/analyze-profile",
        Some(serde_json::to_value(&params).unwrap()),
    )
    .await
    .map_err(|e| e.to_string())
}

/// Detect environment (GPU, Ollama)
#[tauri::command]
pub async fn detect_environment() -> Result<serde_json::Value, String> {
    backend_request(Method::GET, "/api/wizard/environment-detection", None)
        .await
        .map_err(|e| e.to_string())
}

/// Set an API key
#[tauri::command]
pub async fn set_api_key(provider: String, api_key: String) -> Result<(), String> {
    backend_request::<serde_json::Value>(
        Method::POST,
        "/api/keys",
        Some(json!({ "provider": provider, "api_key": api_key })),
    )
    .await
    .map(|_| ())
    .map_err(|e| e.to_string())
}

/// Check if an API key exists
#[tauri::command]
pub async fn has_api_key(provider: String) -> Result<bool, String> {
    #[derive(Deserialize)]
    struct Response {
        exists: bool,
    }

    backend_request::<Response>(
        Method::GET,
        &format!("/api/keys/{}", provider),
        None,
    )
    .await
    .map(|r| r.exists)
    .map_err(|e| e.to_string())
}

/// Delete an API key
#[tauri::command]
pub async fn delete_api_key(provider: String) -> Result<bool, String> {
    backend_request(
        Method::DELETE,
        &format!("/api/keys/{}", provider),
        None,
    )
    .await
    .map_err(|e| e.to_string())
}

// ============================================================================
// Ollama Commands
// ============================================================================

#[derive(Debug, Serialize, Deserialize)]
pub struct OllamaStatus {
    pub installed: bool,
    pub running: bool,
    pub version: Option<String>,
    pub error: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct OllamaModel {
    pub name: String,
    pub size: i64,
    pub size_formatted: String,
    pub digest: String,
    pub modified_at: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct InstallInstructions {
    pub platform: String,
    pub instructions: String,
    pub all_platforms: std::collections::HashMap<String, String>,
}

/// Get Ollama status
#[tauri::command]
pub async fn get_ollama_status() -> Result<OllamaStatus, String> {
    backend_request(Method::GET, "/api/ollama/status", None)
        .await
        .map_err(|e| e.to_string())
}

/// List installed Ollama models
#[tauri::command]
pub async fn list_ollama_models() -> Result<Vec<OllamaModel>, String> {
    backend_request(Method::GET, "/api/ollama/models", None)
        .await
        .map_err(|e| e.to_string())
}

/// Get recommended models
#[tauri::command]
pub async fn get_recommended_models() -> Result<serde_json::Value, String> {
    backend_request(Method::GET, "/api/ollama/recommended", None)
        .await
        .map_err(|e| e.to_string())
}

/// Get Ollama embedding models
#[tauri::command]
pub async fn get_ollama_embedding_models() -> Result<serde_json::Value, String> {
    backend_request(Method::GET, "/api/ollama/embedding-models", None)
        .await
        .map_err(|e| e.to_string())
}

/// Pull (download) an Ollama model
#[tauri::command]
pub async fn pull_ollama_model(model_name: String) -> Result<(), String> {
    backend_request::<serde_json::Value>(
        Method::POST,
        "/api/ollama/pull",
        Some(json!({ "model_name": model_name })),
    )
    .await
    .map(|_| ())
    .map_err(|e| e.to_string())
}

/// Delete an Ollama model
#[tauri::command]
pub async fn delete_ollama_model(model_name: String) -> Result<(), String> {
    backend_request::<serde_json::Value>(
        Method::DELETE,
        "/api/ollama/models",
        Some(json!({ "model_name": model_name })),
    )
    .await
    .map(|_| ())
    .map_err(|e| e.to_string())
}

/// Start Ollama service
#[tauri::command]
pub async fn start_ollama_service() -> Result<(), String> {
    backend_request::<serde_json::Value>(
        Method::POST,
        "/api/ollama/start",
        None,
    )
    .await
    .map(|_| ())
    .map_err(|e| e.to_string())
}

/// Get installation instructions
#[tauri::command]
pub async fn get_install_instructions() -> Result<InstallInstructions, String> {
    backend_request(Method::GET, "/api/ollama/install-instructions", None)
        .await
        .map_err(|e| e.to_string())
}
