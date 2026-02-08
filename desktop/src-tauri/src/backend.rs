//! Backend lifecycle management.
//!
//! In production: launches the bundled ragkit-backend sidecar (PyInstaller executable).
//! In development: launches `python -m ragkit.desktop.main` directly.

use anyhow::{anyhow, Result};
use std::sync::atomic::{AtomicU16, Ordering};
use std::time::Duration;
use tauri::AppHandle;
use tokio::sync::Mutex;
use tokio::time::sleep;

// Global state for backend process
static BACKEND_PORT: AtomicU16 = AtomicU16::new(0);

/// Holds either a sidecar child or a tokio process child.
enum BackendChild {
    Sidecar(tauri_plugin_shell::process::CommandChild),
    Process(tokio::process::Child),
}

static BACKEND_CHILD: Mutex<Option<BackendChild>> = Mutex::const_new(None);

/// Get the backend API base URL.
pub fn get_backend_url() -> String {
    let port = BACKEND_PORT.load(Ordering::Relaxed);
    format!("http://127.0.0.1:{}", port)
}

/// Start the Python backend process.
pub async fn start_backend(app: &AppHandle) -> Result<()> {
    let port = find_available_port().await?;
    BACKEND_PORT.store(port, Ordering::Relaxed);

    tracing::info!("Starting backend on port {}", port);

    let child = if cfg!(debug_assertions) {
        start_dev_backend(port).await?
    } else {
        start_sidecar_backend(app, port)?
    };

    {
        let mut guard = BACKEND_CHILD.lock().await;
        *guard = Some(child);
    }

    wait_for_backend(port, Duration::from_secs(30)).await?;
    tracing::info!("Backend started successfully on port {}", port);
    Ok(())
}

/// Development mode: launch via system Python.
async fn start_dev_backend(port: u16) -> Result<BackendChild> {
    tracing::info!("DEV MODE: launching python -m ragkit.desktop.main");
    let child = tokio::process::Command::new("python")
        .args(["-m", "ragkit.desktop.main", "--port", &port.to_string()])
        .kill_on_drop(true)
        .spawn()
        .map_err(|e| anyhow!("Failed to spawn dev backend: {}", e))?;
    Ok(BackendChild::Process(child))
}

/// Production mode: launch the bundled sidecar executable.
fn start_sidecar_backend(app: &AppHandle, port: u16) -> Result<BackendChild> {
    use tauri_plugin_shell::ShellExt;

    tracing::info!("PRODUCTION: launching ragkit-backend sidecar");

    let sidecar_cmd = app
        .shell()
        .sidecar("ragkit-backend")
        .map_err(|e| anyhow!("Failed to create sidecar command: {}", e))?
        .args(["--port", &port.to_string()]);

    let (mut rx, child) = sidecar_cmd
        .spawn()
        .map_err(|e| anyhow!("Failed to spawn sidecar: {}", e))?;

    // Log sidecar output in a background task
    tauri::async_runtime::spawn(async move {
        use tauri_plugin_shell::process::CommandEvent;
        while let Some(event) = rx.recv().await {
            match event {
                CommandEvent::Stdout(line) => {
                    tracing::info!("[backend stdout] {}", String::from_utf8_lossy(&line));
                }
                CommandEvent::Stderr(line) => {
                    tracing::warn!("[backend stderr] {}", String::from_utf8_lossy(&line));
                }
                CommandEvent::Terminated(payload) => {
                    tracing::info!("[backend] terminated with code: {:?}", payload.code);
                    break;
                }
                CommandEvent::Error(err) => {
                    tracing::error!("[backend] error: {}", err);
                    break;
                }
                _ => {}
            }
        }
    });

    Ok(BackendChild::Sidecar(child))
}

/// Stop the backend process.
pub async fn stop_backend(_app: &AppHandle) {
    tracing::info!("Stopping backend");

    // Try graceful HTTP shutdown first
    let port = BACKEND_PORT.load(Ordering::Relaxed);
    if port > 0 {
        let shutdown_url = format!("http://127.0.0.1:{}/shutdown", port);
        if let Ok(client) = reqwest::Client::builder()
            .timeout(Duration::from_secs(5))
            .build()
        {
            let _ = client.post(&shutdown_url).send().await;
        }
        sleep(Duration::from_millis(500)).await;
    }

    // Force kill
    let mut guard = BACKEND_CHILD.lock().await;
    if let Some(child) = guard.take() {
        match child {
            BackendChild::Sidecar(c) => {
                let _ = c.kill();
            }
            BackendChild::Process(mut c) => {
                let _ = c.kill().await;
            }
        }
    }

    BACKEND_PORT.store(0, Ordering::Relaxed);
    tracing::info!("Backend stopped");
}

/// Find an available port.
async fn find_available_port() -> Result<u16> {
    for port in 8100..8200 {
        let addr = format!("127.0.0.1:{}", port);
        if tokio::net::TcpListener::bind(&addr).await.is_ok() {
            return Ok(port);
        }
    }
    Err(anyhow!("No available port found in range 8100-8199"))
}

/// Wait for the backend /health endpoint to respond.
async fn wait_for_backend(port: u16, timeout: Duration) -> Result<()> {
    let health_url = format!("http://127.0.0.1:{}/health", port);
    let client = reqwest::Client::builder()
        .timeout(Duration::from_secs(2))
        .build()?;

    let start = std::time::Instant::now();
    while start.elapsed() < timeout {
        match client.get(&health_url).send().await {
            Ok(resp) if resp.status().is_success() => return Ok(()),
            _ => sleep(Duration::from_millis(250)).await,
        }
    }

    Err(anyhow!(
        "Backend failed to respond within {} seconds. Check logs at ~/.ragkit/logs/",
        timeout.as_secs()
    ))
}

/// Make an HTTP request to the backend.
pub async fn backend_request<T: serde::de::DeserializeOwned>(
    method: reqwest::Method,
    path: &str,
    body: Option<serde_json::Value>,
) -> Result<T> {
    let url = format!("{}{}", get_backend_url(), path);
    let client = reqwest::Client::new();

    let mut request = client.request(method, &url);
    if let Some(body) = body {
        request = request.json(&body);
    }

    let response = request
        .send()
        .await
        .map_err(|e| anyhow!("Request failed: {}", e))?;

    if !response.status().is_success() {
        let status = response.status();
        let text = response.text().await.unwrap_or_default();
        return Err(anyhow!("Backend error ({}): {}", status, text));
    }

    response
        .json::<T>()
        .await
        .map_err(|e| anyhow!("Failed to parse response: {}", e))
}
