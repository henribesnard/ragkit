// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod backend;
mod commands;

use tauri::Manager;
use tracing_subscriber;

fn main() {
    // Initialize logging
    tracing_subscriber::fmt::init();

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .setup(|app| {
            // Start Python backend on app startup
            let app_handle = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                if let Err(e) = backend::start_backend(&app_handle).await {
                    tracing::error!("Failed to start backend: {}", e);
                }
            });
            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event {
                // Stop backend when window closes
                let app_handle = window.app_handle().clone();
                tauri::async_runtime::spawn(async move {
                    backend::stop_backend(&app_handle).await;
                });
            }
        })
        .invoke_handler(tauri::generate_handler![
            commands::health_check,
            commands::list_knowledge_bases,
            commands::create_knowledge_base,
            commands::delete_knowledge_base,
            commands::add_documents,
            commands::list_conversations,
            commands::create_conversation,
            commands::delete_conversation,
            commands::get_messages,
            commands::query,
            commands::get_settings,
            commands::update_settings,
            commands::set_api_key,
            commands::has_api_key,
            commands::delete_api_key,
            // Ollama commands
            commands::get_ollama_status,
            commands::list_ollama_models,
            commands::get_recommended_models,
            commands::get_ollama_embedding_models,
            commands::pull_ollama_model,
            commands::delete_ollama_model,
            commands::start_ollama_service,
            commands::get_install_instructions,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
