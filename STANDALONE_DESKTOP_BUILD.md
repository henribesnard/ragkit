# RAGKIT Desktop - Plan de build autonome (standalone)

## Objectif

L'utilisateur final telecharge un `.exe` (ou `.msi`), l'installe, double-clique, et tombe directement sur l'interface RAGKIT Desktop. **Aucune installation tierce** (Python, pip, etc.) ne doit etre requise. Tout est embarque dans l'installeur.

---

## Probleme actuel

### Architecture actuelle

```
Installeur (.exe/.msi)
  └── Tauri app (Rust + WebView2 frontend)
        └── backend.rs tente de lancer: python -m ragkit.desktop.main
              └── ECHEC: Python n'est pas embarque dans le bundle
```

### Fichiers concernes

| Fichier | Probleme |
|---------|----------|
| `desktop/src-tauri/src/backend.rs` | En production, cherche `resource_dir/python/python.exe` qui n'existe pas |
| `.github/workflows/release.yml` | Installe Python en CI pour builder mais ne l'embarque PAS dans le bundle |
| `desktop/src-tauri/tauri.conf.json` | Pas de configuration `bundle.resources` ni `bundle.externalBin` pour le backend |
| `desktop/src-tauri/src/main.rs` | Le `.run()` appelait `.expect()` = crash silencieux. **Deja corrige** : logging fichier + dialogue d'erreur natif |

### Consequence

Le `.exe` installe lance la fenetre Tauri (si WebView2 est present), mais le backend Python ne demarre jamais. L'UI reste bloquee sur "Starting RAGKIT backend..." puis affiche "Backend Connection Failed".

Si WebView2 ou le VC++ Runtime manquent, l'app crash silencieusement sans aucun message.

---

## Solution : embarquer le backend Python via PyInstaller

### Architecture cible

```
Installeur (.exe/.msi)
  └── Tauri app (Rust + WebView2 frontend)
        └── backend.rs lance: ragkit-backend.exe (executable autonome PyInstaller)
              └── SUCCES: tout est embarque, aucune dependance externe
```

### Vue d'ensemble des modifications

```
1. Creer le fichier PyInstaller spec       → ragkit-backend.spec (a la racine)
2. Modifier le workflow CI                 → .github/workflows/release.yml
3. Configurer Tauri pour embarquer le .exe → desktop/src-tauri/tauri.conf.json
4. Modifier le code Rust du backend        → desktop/src-tauri/src/backend.rs
5. Configurer l'install auto de WebView2   → desktop/src-tauri/tauri.conf.json
```

---

## Etape 1 : Creer le fichier PyInstaller spec

### Fichier a creer : `ragkit-backend.spec`

Emplacement : racine du projet (`ragkit-backend.spec`)

Ce fichier configure PyInstaller pour compiler `ragkit/desktop/main.py` en un seul executable autonome.

### Contenu du spec

```python
# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for RAGKIT Desktop backend."""

import os
import sys
from pathlib import Path

block_cipher = None

# Project root
project_root = os.path.dirname(os.path.abspath(SPEC))

# Collect data files
datas = [
    # YAML templates needed by ragkit
    (os.path.join(project_root, 'ragkit', 'templates'), os.path.join('ragkit', 'templates')),
]

# Hidden imports that PyInstaller cannot detect automatically
hiddenimports = [
    # ragkit submodules
    'ragkit.agents',
    'ragkit.config',
    'ragkit.config.defaults',
    'ragkit.config.schema',
    'ragkit.desktop',
    'ragkit.desktop.main',
    'ragkit.desktop.api',
    'ragkit.desktop.state',
    'ragkit.embedding',
    'ragkit.embedding.base',
    'ragkit.ingestion',
    'ragkit.ingestion.chunkers',
    'ragkit.ingestion.parsers',
    'ragkit.ingestion.sources',
    'ragkit.ingestion.sources.base',
    'ragkit.llm',
    'ragkit.llm.providers',
    'ragkit.llm.providers.ollama_manager',
    'ragkit.onnx',
    'ragkit.retrieval',
    'ragkit.security',
    'ragkit.security.keyring',
    'ragkit.storage',
    'ragkit.storage.sqlite_store',
    'ragkit.storage.kb_manager',
    'ragkit.storage.conversation_manager',
    'ragkit.vectorstore',
    'ragkit.utils',
    # Third-party
    'litellm',
    'litellm.llms',
    'onnxruntime',
    'tokenizers',
    'huggingface_hub',
    'chromadb',
    'qdrant_client',
    'unstructured',
    'rank_bm25',
    'keyring',
    'keyring.backends',
    'cryptography',
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'fastapi',
    'pydantic',
    'pydantic_settings',
    'httpx',
    'httpcore',
    'structlog',
    'langdetect',
    'yaml',
    'dotenv',
    'numpy',
    'sqlite3',
]

a = Analysis(
    [os.path.join(project_root, 'ragkit', 'desktop', 'main.py')],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclure les modules lourds non necessaires au runtime desktop
        'gradio',
        'matplotlib',
        'tkinter',
        'test',
        'unittest',
        'pytest',
    ],
    noarchive=False,
    optimize=0,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ragkit-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Pas de fenetre console
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon=None,
)
```

### Verification

Apres creation du fichier, verifier qu'il est syntaxiquement correct en ouvrant Python :
```bash
python -c "exec(open('ragkit-backend.spec').read())"
```

Ce test ne buildra pas mais verifie la syntaxe.

---

## Etape 2 : Modifier le workflow CI release

### Fichier a modifier : `.github/workflows/release.yml`

### Modifications

Ajouter une etape PyInstaller **avant** l'etape `Build Tauri app`, pour chaque plateforme.

Remplacer l'etape `Install Python dependencies` actuelle :

```yaml
      - name: Install Python dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[desktop]"
```

Par ces deux etapes :

```yaml
      - name: Install Python dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[desktop]"
          pip install pyinstaller

      - name: Build Python backend executable
        run: |
          pyinstaller ragkit-backend.spec --distpath desktop/src-tauri/binaries
        env:
          PYTHONOPTIMIZE: 1
```

**Important** : Sur chaque plateforme, PyInstaller produit un executable natif :
- Windows : `desktop/src-tauri/binaries/ragkit-backend.exe`
- Linux : `desktop/src-tauri/binaries/ragkit-backend`
- macOS : `desktop/src-tauri/binaries/ragkit-backend`

Tauri Sidecar exige que les binaires soient nommes avec le target triple. Ajouter une etape de renommage apres le build PyInstaller :

```yaml
      - name: Rename backend binary for Tauri sidecar
        shell: bash
        run: |
          cd desktop/src-tauri/binaries
          if [ "${{ runner.os }}" == "Windows" ]; then
            mv ragkit-backend.exe "ragkit-backend-x86_64-pc-windows-msvc.exe"
          elif [ "${{ runner.os }}" == "Linux" ]; then
            mv ragkit-backend "ragkit-backend-x86_64-unknown-linux-gnu"
          elif [ "${{ runner.os }}" == "macOS" ]; then
            if [ "${{ matrix.target }}" == "aarch64-apple-darwin" ]; then
              mv ragkit-backend "ragkit-backend-aarch64-apple-darwin"
            else
              mv ragkit-backend "ragkit-backend-x86_64-apple-darwin"
            fi
          fi
```

### Ordre final des etapes CI (par plateforme)

```
1. Checkout
2. Setup Node
3. Setup Rust
4. Rust cache
5. Install Linux dependencies (Linux only)
6. Setup Python
7. Install Python dependencies + PyInstaller
8. Build Python backend executable (PyInstaller)
9. Rename backend binary for Tauri sidecar
10. Install frontend dependencies
11. Build Tauri app
12. Upload artifacts
```

---

## Etape 3 : Configurer Tauri pour embarquer le backend

### Fichier a modifier : `desktop/src-tauri/tauri.conf.json`

### 3a. Ajouter le sidecar dans `bundle.externalBin`

Ajouter la cle `externalBin` dans la section `bundle` :

```json
{
  "bundle": {
    "active": true,
    "targets": "all",
    "externalBin": [
      "binaries/ragkit-backend"
    ],
    ...
  }
}
```

**Note** : On specifie `binaries/ragkit-backend` sans extension. Tauri ajoute automatiquement le suffixe du target triple et l'extension `.exe` sur Windows.

### 3b. Configurer l'installation automatique de WebView2

Ajouter dans la section `bundle.windows` la configuration NSIS avec le bootstrapper WebView2 :

```json
{
  "bundle": {
    "windows": {
      "certificateThumbprint": null,
      "digestAlgorithm": "sha256",
      "timestampUrl": "",
      "webviewInstallMode": {
        "type": "embedBootstrapper"
      },
      "nsis": {
        "installerIcon": "icons/icon.ico",
        "headerImage": null,
        "sidebarImage": null,
        "installMode": "currentUser",
        "languages": ["French", "English"]
      }
    }
  }
}
```

L'option `"type": "embedBootstrapper"` fait que l'installeur NSIS embarque le bootstrapper WebView2 et l'installe automatiquement si necessaire. L'utilisateur n'a plus besoin de l'installer manuellement.

### 3c. Ajouter la permission sidecar dans le plugin shell

Modifier la section `plugins.shell` pour autoriser l'execution du sidecar :

```json
{
  "plugins": {
    "shell": {
      "open": true,
      "sidecar": true,
      "scope": []
    }
  }
}
```

### 3d. tauri.conf.json complet attendu

```json
{
  "$schema": "https://schema.tauri.app/config/2",
  "productName": "RAGKIT Desktop",
  "version": "1.5.0",
  "identifier": "com.ragkit.desktop",
  "build": {
    "beforeDevCommand": "npm run dev",
    "devUrl": "http://localhost:1420",
    "beforeBuildCommand": "npm run build",
    "frontendDist": "../dist"
  },
  "app": {
    "withGlobalTauri": true,
    "windows": [
      {
        "title": "RAGKIT Desktop",
        "width": 1200,
        "height": 800,
        "minWidth": 800,
        "minHeight": 600,
        "resizable": true,
        "fullscreen": false,
        "center": true
      }
    ],
    "security": {
      "csp": null
    }
  },
  "bundle": {
    "active": true,
    "targets": "all",
    "externalBin": [
      "binaries/ragkit-backend"
    ],
    "icon": [
      "icons/32x32.png",
      "icons/128x128.png",
      "icons/128x128@2x.png",
      "icons/icon.icns",
      "icons/icon.ico"
    ],
    "category": "Productivity",
    "shortDescription": "AI-powered document assistant",
    "longDescription": "RAGKIT Desktop is a local-first AI assistant that helps you search and query your documents using RAG (Retrieval Augmented Generation).",
    "windows": {
      "certificateThumbprint": null,
      "digestAlgorithm": "sha256",
      "timestampUrl": "",
      "webviewInstallMode": {
        "type": "embedBootstrapper"
      },
      "nsis": {
        "installerIcon": "icons/icon.ico",
        "headerImage": null,
        "sidebarImage": null,
        "installMode": "currentUser",
        "languages": ["French", "English"]
      }
    },
    "macOS": {
      "entitlements": null,
      "exceptionDomain": "",
      "frameworks": [],
      "providerShortName": null,
      "signingIdentity": null
    },
    "linux": {
      "deb": {
        "depends": []
      }
    }
  },
  "plugins": {
    "shell": {
      "open": true,
      "sidecar": true,
      "scope": []
    },
    "dialog": {}
  }
}
```

---

## Etape 4 : Modifier backend.rs pour lancer le sidecar

### Fichier a modifier : `desktop/src-tauri/src/backend.rs`

### Remplacement complet du fichier

Le backend.rs doit etre reecrit pour utiliser le sidecar Tauri au lieu de `tokio::process::Command` avec Python.

**Points cles du changement :**

1. En **production** : lancer `ragkit-backend` via l'API sidecar de `tauri-plugin-shell`
2. En **developpement** : continuer a utiliser `python -m ragkit.desktop.main` via `tokio::process::Command`
3. Conserver tout le reste (gestion du port, health check, shutdown, etc.)

### Code complet de remplacement

```rust
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
            BackendChild::Sidecar(c) => { let _ = c.kill(); }
            BackendChild::Process(mut c) => { let _ = c.kill().await; }
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
```

### Verification importante

Le code utilise `tauri_plugin_shell::ShellExt` et `tauri_plugin_shell::process::CommandChild`. Verifier que `tauri-plugin-shell = "2"` est bien dans `Cargo.toml` (c'est deja le cas).

---

## Etape 5 : Creer le dossier binaries avec un placeholder

### Dossier a creer : `desktop/src-tauri/binaries/`

Ce dossier sera vide en local (les binaires sont generes par le CI). Creer un fichier `.gitkeep` :

```
desktop/src-tauri/binaries/.gitkeep
```

Pour le **developpement local**, le dossier peut rester vide car `backend.rs` utilise le mode dev (Python systeme).

---

## Etape 6 : Verifier le main.rs

### Fichier : `desktop/src-tauri/src/main.rs`

Ce fichier a **deja ete corrige** avec :
- Logging vers fichier (`~/.ragkit/logs/ragkit-desktop.log`)
- Dialogue d'erreur natif Windows si `.run()` echoue
- Messages de demarrage informatifs

**Aucune modification supplementaire requise.**

---

## Etape 7 : Verifier la compatibilite Cargo.toml

### Fichier : `desktop/src-tauri/Cargo.toml`

Verifier que ces dependances sont presentes (c'est deja le cas) :

```toml
tauri-plugin-shell = "2"
tauri-plugin-dialog = "2"
tracing = "0.1"
tracing-subscriber = "0.3"
tracing-appender = "0.2"
```

**Aucune modification supplementaire requise.**

---

## Etape 8 : Mettre a jour le .gitignore

### Fichier a modifier : `.gitignore`

Ajouter :

```
# PyInstaller
*.spec.bak
build/
dist/
desktop/src-tauri/binaries/ragkit-backend*
!desktop/src-tauri/binaries/.gitkeep
```

---

## Resume des fichiers a modifier/creer

| Action | Fichier | Description |
|--------|---------|-------------|
| CREER | `ragkit-backend.spec` | Configuration PyInstaller |
| CREER | `desktop/src-tauri/binaries/.gitkeep` | Dossier pour les binaires sidecar |
| MODIFIER | `.github/workflows/release.yml` | Ajouter build PyInstaller + renommage |
| MODIFIER | `desktop/src-tauri/tauri.conf.json` | Ajouter externalBin, webviewInstallMode, sidecar |
| REMPLACER | `desktop/src-tauri/src/backend.rs` | Lancer le sidecar au lieu de Python |
| VERIFIER | `desktop/src-tauri/src/main.rs` | Deja corrige (logging + error dialog) |
| VERIFIER | `desktop/src-tauri/Cargo.toml` | Deja correct |
| MODIFIER | `.gitignore` | Ignorer les binaires PyInstaller |

---

## Checklist de validation

Apres implementation, verifier les points suivants :

### Build local (dev)
- [ ] `cd desktop && npm run tauri dev` fonctionne
- [ ] Le backend Python se lance via `python -m ragkit.desktop.main`
- [ ] L'interface s'affiche et repond au health check
- [ ] Pas de regression sur les fonctionnalites existantes

### Build CI (release)
- [ ] Le workflow `release.yml` se declenche sur un tag `v*`
- [ ] PyInstaller compile le backend sans erreur pour chaque plateforme
- [ ] Le binaire est renomme avec le target triple correct
- [ ] Tauri build reussit en incluant le sidecar
- [ ] Les artefacts (`.exe`, `.msi`, `.dmg`, `.AppImage`, `.deb`) sont generes

### Installation Windows (test final)
- [ ] Telecharger le `.exe` depuis les releases
- [ ] Double-cliquer sur l'installeur
- [ ] WebView2 s'installe automatiquement si absent
- [ ] L'app se lance depuis le menu Demarrer
- [ ] La fenetre RAGKIT Desktop apparait
- [ ] Le backend demarre (le loading screen se termine)
- [ ] L'ecran d'onboarding s'affiche
- [ ] Navigation dans Settings, Chat, Knowledge Bases fonctionne
- [ ] Les logs sont ecrits dans `%USERPROFILE%\.ragkit\logs\`

### Points d'attention
- Le binaire PyInstaller pour Windows fait environ 100-200 Mo (toutes les libs Python embarquees). C'est normal.
- Le premier demarrage peut etre plus lent (decompression du binaire PyInstaller).
- `console=False` dans le spec PyInstaller est important pour ne pas afficher de fenetre console parasite.
- Sur macOS, le binaire PyInstaller doit etre signe pour passer Gatekeeper (ou l'utilisateur fait clic droit > Ouvrir).

---

## Workflow de developpement vs production

```
DEVELOPPEMENT (npm run tauri dev)
  └── backend.rs detecte cfg!(debug_assertions) = true
        └── Lance: python -m ragkit.desktop.main --port 8100
              └── Necessite Python + pip install -e ".[desktop]" en local

PRODUCTION (installeur release)
  └── backend.rs detecte cfg!(debug_assertions) = false
        └── Lance: ragkit-backend sidecar (via tauri-plugin-shell)
              └── Executable PyInstaller autonome, aucune dependance
```
