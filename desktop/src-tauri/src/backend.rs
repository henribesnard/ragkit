//! Backend lifecycle management for the Python sidecar process.

use anyhow::{anyhow, Result};
use std::sync::atomic::{AtomicU16, Ordering};
use std::time::Duration;
use tauri::{AppHandle, Manager};
use tokio::process::{Child, Command};
use tokio::sync::Mutex;
use tokio::time::sleep;

// Global state for backend process
static BACKEND_PORT: AtomicU16 = AtomicU16::new(0);
static BACKEND_PROCESS: Mutex<Option<Child>> = Mutex::const_new(None);

/// Get the backend API base URL
pub fn get_backend_url() -> String {
    let port = BACKEND_PORT.load(Ordering::Relaxed);
    format!("http://127.0.0.1:{}", port)
}

/// Start the Python backend process
pub async fn start_backend(app: &AppHandle) -> Result<()> {
    // Find an available port
    let port = find_available_port().await?;
    BACKEND_PORT.store(port, Ordering::Relaxed);

    tracing::info!("Starting Python backend on port {}", port);

    // Get the path to the Python executable
    // In development, we use the system Python
    // In production, we bundle Python as a sidecar
    let python_cmd = if cfg!(debug_assertions) {
        "python".to_string()
    } else {
        // Look for bundled Python in resources
        let resource_path = app.path().resource_dir()
            .map_err(|e| anyhow!("Failed to get resource dir: {}", e))?;

        #[cfg(target_os = "windows")]
        let python_path = resource_path.join("python").join("python.exe");
        #[cfg(not(target_os = "windows"))]
        let python_path = resource_path.join("python").join("bin").join("python3");

        python_path.to_string_lossy().to_string()
    };

    // Start the backend process
    let child = Command::new(&python_cmd)
        .args([
            "-m",
            "ragkit.desktop.main",
            "--port",
            &port.to_string(),
        ])
        .kill_on_drop(true)
        .spawn()
        .map_err(|e| anyhow!("Failed to spawn backend process: {}", e))?;

    // Store the process handle
    {
        let mut process = BACKEND_PROCESS.lock().await;
        *process = Some(child);
    }

    // Wait for backend to be ready
    wait_for_backend(port, Duration::from_secs(30)).await?;

    tracing::info!("Python backend started successfully");
    Ok(())
}

/// Stop the Python backend process
pub async fn stop_backend(_app: &AppHandle) {
    tracing::info!("Stopping Python backend");

    let mut process = BACKEND_PROCESS.lock().await;
    if let Some(mut child) = process.take() {
        // Try graceful shutdown first
        let port = BACKEND_PORT.load(Ordering::Relaxed);
        let shutdown_url = format!("http://127.0.0.1:{}/shutdown", port);

        if let Ok(client) = reqwest::Client::builder()
            .timeout(Duration::from_secs(5))
            .build()
        {
            let _ = client.post(&shutdown_url).send().await;
        }

        // Give it a moment to shut down gracefully
        sleep(Duration::from_millis(500)).await;

        // Force kill if still running
        let _ = child.kill().await;
    }

    BACKEND_PORT.store(0, Ordering::Relaxed);
    tracing::info!("Python backend stopped");
}

/// Find an available port for the backend
async fn find_available_port() -> Result<u16> {
    // Try ports in range 8100-8199
    for port in 8100..8200 {
        let addr = format!("127.0.0.1:{}", port);
        if tokio::net::TcpListener::bind(&addr).await.is_ok() {
            return Ok(port);
        }
    }
    Err(anyhow!("No available port found"))
}

/// Wait for the backend to be ready
async fn wait_for_backend(port: u16, timeout: Duration) -> Result<()> {
    let health_url = format!("http://127.0.0.1:{}/health", port);
    let client = reqwest::Client::builder()
        .timeout(Duration::from_secs(2))
        .build()?;

    let start = std::time::Instant::now();

    while start.elapsed() < timeout {
        match client.get(&health_url).send().await {
            Ok(resp) if resp.status().is_success() => {
                return Ok(());
            }
            _ => {
                sleep(Duration::from_millis(250)).await;
            }
        }
    }

    Err(anyhow!("Backend failed to start within {} seconds", timeout.as_secs()))
}

/// Make an HTTP request to the backend
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

    let response = request.send().await
        .map_err(|e| anyhow!("Request failed: {}", e))?;

    if !response.status().is_success() {
        let status = response.status();
        let text = response.text().await.unwrap_or_default();
        return Err(anyhow!("Backend error ({}): {}", status, text));
    }

    response.json::<T>().await
        .map_err(|e| anyhow!("Failed to parse response: {}", e))
}
