// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod backend;
mod commands;

use tauri::Manager;

/// Get the log directory path (~/.ragkit/logs/)
fn get_log_dir() -> std::path::PathBuf {
    #[cfg(target_os = "windows")]
    let home = std::env::var("USERPROFILE").unwrap_or_else(|_| "C:\\".to_string());
    #[cfg(not(target_os = "windows"))]
    let home = std::env::var("HOME").unwrap_or_else(|_| "/tmp".to_string());

    std::path::PathBuf::from(home).join(".ragkit").join("logs")
}

/// Show a native error dialog on Windows (no dependencies needed)
#[cfg(target_os = "windows")]
fn show_error_dialog(title: &str, message: &str) {
    use std::ffi::OsStr;
    use std::iter::once;
    use std::os::windows::ffi::OsStrExt;

    extern "system" {
        fn MessageBoxW(
            hwnd: *mut std::ffi::c_void,
            text: *const u16,
            caption: *const u16,
            utype: u32,
        ) -> i32;
    }

    let text: Vec<u16> = OsStr::new(message).encode_wide().chain(once(0)).collect();
    let caption: Vec<u16> = OsStr::new(title).encode_wide().chain(once(0)).collect();

    unsafe {
        // MB_ICONERROR = 0x10
        MessageBoxW(std::ptr::null_mut(), text.as_ptr(), caption.as_ptr(), 0x10);
    }
}

#[cfg(not(target_os = "windows"))]
fn show_error_dialog(_title: &str, message: &str) {
    eprintln!("{}", message);
}

fn main() {
    // Initialize file-based logging (visible even in release mode on Windows)
    let log_dir = get_log_dir();
    let _ = std::fs::create_dir_all(&log_dir);

    let file_appender = tracing_appender::rolling::daily(&log_dir, "ragkit-desktop.log");

    tracing_subscriber::fmt()
        .with_writer(file_appender)
        .with_ansi(false)
        .init();

    tracing::info!("=== RAGKIT Desktop starting ===");
    tracing::info!("Version: {}", env!("CARGO_PKG_VERSION"));
    tracing::info!(
        "Log directory: {}",
        log_dir.display()
    );

    let result = tauri::Builder::default()
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
            commands::add_folder,
            commands::validate_folder,
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
            commands::test_api_key,
            commands::get_logs,
            commands::clear_logs,
            commands::analyze_wizard_profile,
            commands::detect_environment,
            // Ollama commands
            commands::get_ollama_status,
            commands::list_ollama_models,
            commands::get_recommended_models,
            commands::get_ollama_embedding_models,
            commands::pull_ollama_model,
            commands::delete_ollama_model,
            commands::start_ollama_service,
            commands::get_install_instructions,
            commands::preview_ingestion,
        ])
        .run(tauri::generate_context!());

    if let Err(e) = result {
        let error_msg = format!(
            "RAGKIT Desktop failed to start:\n\n{}\n\n\
            Possible fixes:\n\
            - Install Microsoft Edge WebView2 Runtime\n\
            - Install Visual C++ Redistributable (x64)\n\
            - Check logs at: {}",
            e,
            log_dir.display()
        );
        tracing::error!("{}", error_msg);
        show_error_dialog("RAGKIT Desktop - Startup Error", &error_msg);
    }
}
