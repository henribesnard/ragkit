# RAGKIT Desktop - Spécifications Techniques

## 📋 Informations du Document

| Champ | Valeur |
|-------|--------|
| **Version** | 0.1 (Draft) |
| **Date** | 05/02/2026 |
| **Statut** | Proposition |
| **Auteur** | RAGKIT Team |

---

## 🎯 Vision Produit

### Objectif

Transformer RAGKIT en une **application de bureau autonome** permettant à n'importe quel utilisateur (technique ou non) de créer et interroger une base de connaissances personnelle à partir de ses documents, **sans installation complexe ni dépendances externes obligatoires**.

### Proposition de valeur

> "Installez RAGKIT, pointez vers vos documents, posez vos questions."

- **Zero friction** : Un seul installateur, pas de Docker/Python/CLI
- **Privacy-first** : Données locales par défaut, API externes optionnelles
- **Flexible** : Du mode 100% local au mode cloud partagé

### Utilisateurs cibles

| Persona | Besoin principal | Mode privilégié |
|---------|------------------|-----------------|
| **Professionnel individuel** | Questionner ses documents de travail | Desktop local |
| **Équipe technique** | Base de connaissances partagée | Self-hosted server |
| **Entreprise** | RAG multi-utilisateurs avec RBAC | Cloud privé |
| **Grand public** | Assistant personnel sur ses fichiers | Desktop local |

---

## 🏗️ Architecture Technique

### Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         RAGKIT DESKTOP v2                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                        UI Layer (Tauri + WebView)                   │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │ │
│  │  │ Onboard  │  │  Config  │  │   Chat   │  │  Document        │   │ │
│  │  │  Wizard  │  │  Panel   │  │Interface │  │  Browser         │   │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘   │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                              │ IPC / HTTP                                │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                     Backend Layer (Python/FastAPI)                  │ │
│  │                                                                      │ │
│  │  ┌─────────────────────────────────────────────────────────────┐   │ │
│  │  │                    Core RAGKIT Engine                        │   │ │
│  │  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌──────────┐ │   │ │
│  │  │  │ Ingestion │  │ Retrieval │  │  Agents   │  │   API    │ │   │ │
│  │  │  │ Pipeline  │  │  Engine   │  │  System   │  │ Server   │ │   │ │
│  │  │  └───────────┘  └───────────┘  └───────────┘  └──────────┘ │   │ │
│  │  └─────────────────────────────────────────────────────────────┘   │ │
│  │                                                                      │ │
│  │  ┌─────────────────────────────────────────────────────────────┐   │ │
│  │  │                   Provider Layer (Pluggable)                 │   │ │
│  │  │                                                               │   │ │
│  │  │  ┌─────────────────────────────────────────────────────────┐ │   │ │
│  │  │  │ EMBEDDING PROVIDERS                                      │ │   │ │
│  │  │  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐ │ │   │ │
│  │  │  │  │ ONNX Local │  │  Ollama    │  │  External APIs     │ │ │   │ │
│  │  │  │  │ (embedded) │  │  (local)   │  │  (OpenAI/Cohere)   │ │ │   │ │
│  │  │  │  └────────────┘  └────────────┘  └────────────────────┘ │ │   │ │
│  │  │  └─────────────────────────────────────────────────────────┘ │   │ │
│  │  │                                                               │   │ │
│  │  │  ┌─────────────────────────────────────────────────────────┐ │   │ │
│  │  │  │ LLM PROVIDERS                                            │ │   │ │
│  │  │  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐ │ │   │ │
│  │  │  │  │  Ollama    │  │ llama.cpp  │  │  External APIs     │ │ │   │ │
│  │  │  │  │  (local)   │  │  (future)  │  │  (OpenAI/Claude)   │ │ │   │ │
│  │  │  │  └────────────┘  └────────────┘  └────────────────────┘ │ │   │ │
│  │  │  └─────────────────────────────────────────────────────────┘ │   │ │
│  │  │                                                               │   │ │
│  │  │  ┌─────────────────────────────────────────────────────────┐ │   │ │
│  │  │  │ STORAGE PROVIDERS                                        │ │   │ │
│  │  │  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐ │ │   │ │
│  │  │  │  │  ChromaDB  │  │  SQLite    │  │  PostgreSQL        │ │ │   │ │
│  │  │  │  │ (vectors)  │  │ (metadata) │  │  (server mode)     │ │ │   │ │
│  │  │  │  └────────────┘  └────────────┘  └────────────────────┘ │ │   │ │
│  │  │  └─────────────────────────────────────────────────────────┘ │   │ │
│  │  └─────────────────────────────────────────────────────────────┘   │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                      Local Storage                                  │ │
│  │  ~/ragkit/                                                          │ │
│  │  ├── config.yaml          # Configuration utilisateur               │ │
│  │  ├── ragkit.db            # SQLite (metadata, sessions, users)      │ │
│  │  ├── vectors/             # ChromaDB persistent storage             │ │
│  │  ├── models/              # ONNX models cache                       │ │
│  │  └── logs/                # Application logs                        │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Composants Détaillés

### 1. UI Layer (Tauri Shell)

#### Technologie choisie : Tauri

| Critère | Tauri | Electron | PyQt/PySide |
|---------|-------|----------|-------------|
| Taille bundle | ~10 MB | ~150 MB | ~50 MB |
| RAM usage | Faible | Élevée | Moyenne |
| UI moderne | ✅ (Web) | ✅ (Web) | ⚠️ |
| Cross-platform | ✅ | ✅ | ✅ |
| Intégration Python | Via sidecar | Via spawn | Native |

**Choix : Tauri avec Python sidecar**

#### Écrans principaux

```
1. Onboarding Wizard
   ├── Welcome screen
   ├── Provider selection (Local vs API)
   ├── API keys input (optional)
   ├── First knowledge base creation
   └── Tutorial overlay

2. Main Dashboard
   ├── Knowledge bases list
   ├── Quick stats (docs, chunks, queries)
   ├── Recent conversations
   └── System status (Ollama, storage)

3. Chat Interface
   ├── Conversation history
   ├── Message input
   ├── Source citations (expandable)
   ├── Streaming response display
   └── Export conversation

4. Configuration Panel
   ├── General settings
   ├── Provider configuration
   │   ├── Embedding provider (ONNX/Ollama/API)
   │   ├── LLM provider (Ollama/API)
   │   └── API keys management
   ├── Knowledge bases management
   ├── Ingestion settings
   └── Advanced settings

5. Document Browser
   ├── Source files tree
   ├── Document preview
   ├── Chunk visualization
   └── Re-ingestion controls
```

#### Communication UI ↔ Backend

```typescript
// Tauri IPC Commands
interface RagkitCommands {
  // Knowledge Base
  createKnowledgeBase(config: KBConfig): Promise<string>;
  listKnowledgeBases(): Promise<KnowledgeBase[]>;
  deleteKnowledgeBase(id: string): Promise<void>;
  
  // Ingestion
  ingestDocuments(kbId: string, paths: string[]): Promise<IngestResult>;
  getIngestionStatus(jobId: string): Promise<IngestStatus>;
  
  // Query
  query(kbId: string, question: string): Promise<QueryResult>;
  queryStream(kbId: string, question: string): AsyncIterator<Chunk>;
  
  // Configuration
  getConfig(): Promise<AppConfig>;
  updateConfig(config: Partial<AppConfig>): Promise<void>;
  testProvider(provider: ProviderConfig): Promise<TestResult>;
  
  // System
  getSystemStatus(): Promise<SystemStatus>;
  downloadModel(modelId: string): Promise<void>;
}
```

---

### 2. Embedding Providers

#### 2.1 ONNX Local Embedder (Nouveau - Priorité P0)

**Objectif** : Embeddings 100% locaux sans dépendance externe.

```python
# ragkit/embedding/providers/onnx_local.py

"""ONNX Runtime local embedding provider."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import numpy as np

from ragkit.config.schema import EmbeddingModelConfig
from ragkit.embedding.base import BaseEmbedder
from ragkit.exceptions import EmbeddingError


# Modèles ONNX supportés avec leurs caractéristiques
SUPPORTED_MODELS = {
    "all-MiniLM-L6-v2": {
        "dimensions": 384,
        "max_tokens": 256,
        "size_mb": 90,
        "url": "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2",
        "description": "Fast, good quality, small size",
    },
    "all-mpnet-base-v2": {
        "dimensions": 768,
        "max_tokens": 384,
        "size_mb": 420,
        "url": "https://huggingface.co/sentence-transformers/all-mpnet-base-v2",
        "description": "Higher quality, larger size",
    },
    "multilingual-e5-small": {
        "dimensions": 384,
        "max_tokens": 512,
        "size_mb": 470,
        "url": "https://huggingface.co/intfloat/multilingual-e5-small",
        "description": "Multilingual support (French included)",
    },
    "bge-small-en-v1.5": {
        "dimensions": 384,
        "max_tokens": 512,
        "size_mb": 130,
        "url": "https://huggingface.co/BAAI/bge-small-en-v1.5",
        "description": "SOTA small English model",
    },
}

DEFAULT_MODEL = "all-MiniLM-L6-v2"


class ONNXLocalEmbedder(BaseEmbedder):
    """Local embedding using ONNX Runtime."""

    def __init__(self, config: EmbeddingModelConfig):
        self.config = config
        self.model_name = config.model or DEFAULT_MODEL
        
        if self.model_name not in SUPPORTED_MODELS:
            raise EmbeddingError(f"Unsupported ONNX model: {self.model_name}")
        
        self.model_info = SUPPORTED_MODELS[self.model_name]
        self._dimensions = self.model_info["dimensions"]
        
        # Lazy loading
        self._session = None
        self._tokenizer = None
        
    def _ensure_model_downloaded(self) -> Path:
        """Download model if not present."""
        models_dir = Path.home() / ".ragkit" / "models" / "onnx"
        model_path = models_dir / self.model_name
        
        if not model_path.exists():
            self._download_model(model_path)
        
        return model_path
    
    def _download_model(self, target_path: Path) -> None:
        """Download ONNX model from HuggingFace."""
        # Implementation: use huggingface_hub or direct download
        # Show progress in UI via callback
        raise NotImplementedError("Model download not yet implemented")
    
    def _load_model(self) -> None:
        """Load ONNX model and tokenizer."""
        try:
            import onnxruntime as ort
            from tokenizers import Tokenizer
        except ImportError as e:
            raise EmbeddingError(
                "onnxruntime and tokenizers are required for local embedding. "
                "Install with: pip install onnxruntime tokenizers"
            ) from e
        
        model_path = self._ensure_model_downloaded()
        
        # Load ONNX session
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        
        # Use available providers (CUDA if available, else CPU)
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        available_providers = ort.get_available_providers()
        providers = [p for p in providers if p in available_providers]
        
        self._session = ort.InferenceSession(
            str(model_path / "model.onnx"),
            sess_options,
            providers=providers,
        )
        
        # Load tokenizer
        self._tokenizer = Tokenizer.from_file(str(model_path / "tokenizer.json"))
        self._tokenizer.enable_truncation(max_length=self.model_info["max_tokens"])
        self._tokenizer.enable_padding(length=self.model_info["max_tokens"])

    @property
    def dimensions(self) -> int:
        return self._dimensions

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if self._session is None:
            self._load_model()
        
        # Tokenize
        encoded = self._tokenizer.encode_batch(texts)
        
        input_ids = np.array([e.ids for e in encoded], dtype=np.int64)
        attention_mask = np.array([e.attention_mask for e in encoded], dtype=np.int64)
        
        # Run inference
        outputs = self._session.run(
            None,
            {
                "input_ids": input_ids,
                "attention_mask": attention_mask,
            },
        )
        
        # Mean pooling
        embeddings = self._mean_pooling(outputs[0], attention_mask)
        
        # Normalize
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        
        return embeddings.tolist()

    async def embed_query(self, query: str) -> list[float]:
        results = await self.embed([query])
        return results[0]
    
    def _mean_pooling(
        self, 
        token_embeddings: np.ndarray, 
        attention_mask: np.ndarray
    ) -> np.ndarray:
        """Apply mean pooling to token embeddings."""
        mask_expanded = np.expand_dims(attention_mask, axis=-1)
        sum_embeddings = np.sum(token_embeddings * mask_expanded, axis=1)
        sum_mask = np.clip(np.sum(mask_expanded, axis=1), a_min=1e-9, a_max=None)
        return sum_embeddings / sum_mask
```

**Configuration YAML pour ONNX :**

```yaml
embedding:
  document_model:
    provider: "onnx_local"
    model: "all-MiniLM-L6-v2"  # ou multilingual-e5-small pour FR
    params:
      batch_size: 32
    cache:
      enabled: true
      backend: "disk"
  query_model:
    provider: "onnx_local"
    model: "all-MiniLM-L6-v2"
```

#### 2.2 Providers externes (existants)

Les providers OpenAI, Cohere, Ollama restent disponibles si l'utilisateur fournit des clés API.

**Interface de configuration UI :**

```
┌─────────────────────────────────────────────────────────────┐
│  Embedding Provider Configuration                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ○ Local (ONNX) - Recommended for privacy                  │
│    └─ Model: [all-MiniLM-L6-v2 ▼]                          │
│       Size: 90 MB | Quality: Good | Speed: Fast            │
│                                                             │
│  ○ Local (Ollama) - Requires Ollama installed              │
│    └─ Model: [nomic-embed-text ▼]                          │
│       Status: ● Connected                                   │
│                                                             │
│  ○ Cloud API - Requires API key                            │
│    └─ Provider: [OpenAI ▼]                                 │
│       Model: [text-embedding-3-small ▼]                    │
│       API Key: [••••••••••••••••] [Test]                   │
│                                                             │
│  [Download Model]  [Apply]  [Cancel]                       │
└─────────────────────────────────────────────────────────────┘
```

---

### 3. LLM Providers

#### 3.1 Stratégie LLM

Contrairement à l'embedding, embarquer un LLM est complexe (taille, performance). 

**Approche recommandée :**

| Mode | Provider | Prérequis | Performance |
|------|----------|-----------|-------------|
| **Local recommandé** | Ollama | Installation Ollama | Bonne (avec GPU) |
| **Local embarqué** | llama.cpp (futur) | Aucun | Moyenne |
| **Cloud** | OpenAI/Anthropic | Clé API | Excellente |

#### 3.2 Intégration Ollama améliorée

```python
# ragkit/llm/providers/ollama_manager.py

"""Ollama management and integration."""

from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path

import httpx

OLLAMA_API_URL = "http://localhost:11434"

RECOMMENDED_MODELS = {
    "llama3.2:3b": {
        "size_gb": 2.0,
        "quality": "good",
        "speed": "fast",
        "description": "Balanced performance for most tasks",
    },
    "llama3.1:8b": {
        "size_gb": 4.7,
        "quality": "excellent",
        "speed": "medium",
        "description": "High quality, needs good GPU",
    },
    "mistral:7b": {
        "size_gb": 4.1,
        "quality": "excellent",
        "speed": "medium",
        "description": "Great for reasoning tasks",
    },
    "phi3:mini": {
        "size_gb": 2.2,
        "quality": "good",
        "speed": "very fast",
        "description": "Microsoft's efficient small model",
    },
    "qwen2.5:3b": {
        "size_gb": 1.9,
        "quality": "good",
        "speed": "fast",
        "description": "Good multilingual support",
    },
}


class OllamaManager:
    """Manage Ollama installation and models."""

    def __init__(self, api_url: str = OLLAMA_API_URL):
        self.api_url = api_url
        self._client = httpx.AsyncClient(timeout=300)

    async def is_installed(self) -> bool:
        """Check if Ollama is installed and running."""
        try:
            response = await self._client.get(f"{self.api_url}/api/version")
            return response.status_code == 200
        except httpx.ConnectError:
            return False

    async def get_version(self) -> str | None:
        """Get Ollama version."""
        try:
            response = await self._client.get(f"{self.api_url}/api/version")
            if response.status_code == 200:
                return response.json().get("version")
        except Exception:
            pass
        return None

    async def list_models(self) -> list[dict]:
        """List installed models."""
        try:
            response = await self._client.get(f"{self.api_url}/api/tags")
            if response.status_code == 200:
                return response.json().get("models", [])
        except Exception:
            pass
        return []

    async def pull_model(
        self, 
        model_name: str, 
        progress_callback: callable | None = None
    ) -> bool:
        """Pull a model with progress tracking."""
        try:
            async with self._client.stream(
                "POST",
                f"{self.api_url}/api/pull",
                json={"name": model_name},
            ) as response:
                async for line in response.aiter_lines():
                    if progress_callback and line:
                        import json
                        data = json.loads(line)
                        progress_callback(data)
            return True
        except Exception:
            return False

    async def check_model_available(self, model_name: str) -> bool:
        """Check if a specific model is available."""
        models = await self.list_models()
        return any(m.get("name", "").startswith(model_name) for m in models)

    def get_install_instructions(self) -> dict:
        """Get OS-specific installation instructions."""
        if sys.platform == "darwin":
            return {
                "os": "macOS",
                "method": "brew",
                "command": "brew install ollama",
                "url": "https://ollama.ai/download/mac",
            }
        elif sys.platform == "win32":
            return {
                "os": "Windows",
                "method": "installer",
                "command": None,
                "url": "https://ollama.ai/download/windows",
            }
        else:
            return {
                "os": "Linux",
                "method": "script",
                "command": "curl -fsSL https://ollama.ai/install.sh | sh",
                "url": "https://ollama.ai/download/linux",
            }
```

#### 3.3 Configuration UI pour LLM

```
┌─────────────────────────────────────────────────────────────┐
│  LLM Provider Configuration                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ○ Local (Ollama) - Recommended                            │
│    │                                                        │
│    │  Status: ● Ollama running (v0.3.12)                   │
│    │                                                        │
│    │  Installed Models:                                     │
│    │  ┌─────────────────────────────────────────────────┐  │
│    │  │ ● llama3.2:3b     2.0 GB   [Use] [Delete]      │  │
│    │  │ ○ mistral:7b      4.1 GB   [Use] [Delete]      │  │
│    │  └─────────────────────────────────────────────────┘  │
│    │                                                        │
│    │  Download new model: [phi3:mini ▼] [Download]         │
│    │                                                        │
│    └─ Selected: llama3.2:3b                                │
│                                                             │
│  ○ Cloud API                                               │
│    └─ Provider: [OpenAI ▼]                                 │
│       Model: [gpt-4o-mini ▼]                               │
│       API Key: [••••••••••••••••] [Test]                   │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│  ⚠️  Ollama not installed?                                  │
│     [Download Ollama] [Installation Guide]                  │
│                                                             │
│  [Apply]  [Cancel]                                         │
└─────────────────────────────────────────────────────────────┘
```

---

### 4. Storage Layer

#### 4.1 SQLite pour les métadonnées

**Nouveau fichier : `ragkit/storage/sqlite_store.py`**

```python
"""SQLite storage for application state and metadata."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Generator
from uuid import uuid4

from pydantic import BaseModel


class KnowledgeBase(BaseModel):
    id: str
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    config: dict[str, Any]
    stats: dict[str, Any]


class Conversation(BaseModel):
    id: str
    kb_id: str
    title: str | None
    created_at: datetime
    updated_at: datetime


class Message(BaseModel):
    id: str
    conversation_id: str
    role: str  # user | assistant
    content: str
    sources: list[str]
    metadata: dict[str, Any]
    created_at: datetime


class SQLiteStore:
    """SQLite storage for RAGKIT Desktop."""

    SCHEMA_VERSION = 1

    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        """Initialize database schema."""
        with self._connection() as conn:
            conn.executescript("""
                -- Schema version tracking
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY
                );
                
                -- Knowledge bases
                CREATE TABLE IF NOT EXISTS knowledge_bases (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    config TEXT NOT NULL,  -- JSON
                    stats TEXT DEFAULT '{}',  -- JSON
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Documents (source files)
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    kb_id TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    file_type TEXT,
                    file_hash TEXT,
                    chunk_count INTEGER DEFAULT 0,
                    metadata TEXT DEFAULT '{}',  -- JSON
                    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE
                );
                
                -- Conversations
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    kb_id TEXT NOT NULL,
                    title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE
                );
                
                -- Messages
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    sources TEXT DEFAULT '[]',  -- JSON array
                    metadata TEXT DEFAULT '{}',  -- JSON
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                );
                
                -- API Keys (encrypted)
                CREATE TABLE IF NOT EXISTS api_keys (
                    id TEXT PRIMARY KEY,
                    provider TEXT NOT NULL,
                    encrypted_key TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Application settings
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Indexes
                CREATE INDEX IF NOT EXISTS idx_documents_kb ON documents(kb_id);
                CREATE INDEX IF NOT EXISTS idx_conversations_kb ON conversations(kb_id);
                CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id);
            """)

    # Knowledge Base operations
    def create_knowledge_base(
        self, 
        name: str, 
        description: str | None = None,
        config: dict | None = None
    ) -> KnowledgeBase:
        kb_id = str(uuid4())
        now = datetime.utcnow()
        config = config or {}
        
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO knowledge_bases (id, name, description, config, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (kb_id, name, description, json.dumps(config), now, now)
            )
        
        return KnowledgeBase(
            id=kb_id,
            name=name,
            description=description,
            created_at=now,
            updated_at=now,
            config=config,
            stats={},
        )

    def list_knowledge_bases(self) -> list[KnowledgeBase]:
        with self._connection() as conn:
            rows = conn.execute("SELECT * FROM knowledge_bases ORDER BY updated_at DESC").fetchall()
        
        return [
            KnowledgeBase(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                config=json.loads(row["config"]),
                stats=json.loads(row["stats"]),
            )
            for row in rows
        ]

    def get_knowledge_base(self, kb_id: str) -> KnowledgeBase | None:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM knowledge_bases WHERE id = ?", (kb_id,)
            ).fetchone()
        
        if not row:
            return None
        
        return KnowledgeBase(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            config=json.loads(row["config"]),
            stats=json.loads(row["stats"]),
        )

    def delete_knowledge_base(self, kb_id: str) -> bool:
        with self._connection() as conn:
            cursor = conn.execute("DELETE FROM knowledge_bases WHERE id = ?", (kb_id,))
        return cursor.rowcount > 0

    # Conversation operations
    def create_conversation(self, kb_id: str, title: str | None = None) -> Conversation:
        conv_id = str(uuid4())
        now = datetime.utcnow()
        
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO conversations (id, kb_id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (conv_id, kb_id, title, now, now)
            )
        
        return Conversation(
            id=conv_id,
            kb_id=kb_id,
            title=title,
            created_at=now,
            updated_at=now,
        )

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        sources: list[str] | None = None,
        metadata: dict | None = None,
    ) -> Message:
        msg_id = str(uuid4())
        now = datetime.utcnow()
        sources = sources or []
        metadata = metadata or {}
        
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO messages (id, conversation_id, role, content, sources, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (msg_id, conversation_id, role, content, json.dumps(sources), json.dumps(metadata), now)
            )
            conn.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (now, conversation_id)
            )
        
        return Message(
            id=msg_id,
            conversation_id=conversation_id,
            role=role,
            content=content,
            sources=sources,
            metadata=metadata,
            created_at=now,
        )

    def get_conversation_messages(self, conversation_id: str) -> list[Message]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at",
                (conversation_id,)
            ).fetchall()
        
        return [
            Message(
                id=row["id"],
                conversation_id=row["conversation_id"],
                role=row["role"],
                content=row["content"],
                sources=json.loads(row["sources"]),
                metadata=json.loads(row["metadata"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    # Settings operations
    def get_setting(self, key: str, default: Any = None) -> Any:
        with self._connection() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        
        if row:
            return json.loads(row["value"])
        return default

    def set_setting(self, key: str, value: Any) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO settings (key, value, updated_at) VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = ?
                """,
                (key, json.dumps(value), datetime.utcnow(), json.dumps(value), datetime.utcnow())
            )
```

#### 4.2 ChromaDB pour les vecteurs

ChromaDB reste le vector store par défaut en mode persistent :

```yaml
vector_store:
  provider: "chroma"
  chroma:
    mode: "persistent"
    path: "~/.ragkit/vectors/{kb_id}"  # Un répertoire par knowledge base
    collection_name: "documents"
```

---

### 5. Configuration Unifiée

#### 5.1 Structure de configuration Desktop

```yaml
# ~/.ragkit/config.yaml

version: "2.0"

# Application settings
app:
  mode: "desktop"  # desktop | server
  language: "auto"  # auto | fr | en
  theme: "system"  # light | dark | system
  
  # First run wizard completed
  onboarding_complete: true
  
  # Telemetry (opt-in)
  telemetry:
    enabled: false
    anonymous: true

# Default provider configuration
providers:
  embedding:
    default: "onnx_local"
    
    onnx_local:
      model: "all-MiniLM-L6-v2"
      
    ollama:
      model: "nomic-embed-text"
      
    openai:
      model: "text-embedding-3-small"
      api_key_ref: "openai"  # Reference to stored key
      
    cohere:
      model: "embed-multilingual-v3.0"
      api_key_ref: "cohere"

  llm:
    default: "ollama"
    
    ollama:
      model: "llama3.2:3b"
      
    openai:
      model: "gpt-4o-mini"
      api_key_ref: "openai"
      
    anthropic:
      model: "claude-sonnet-4-20250514"
      api_key_ref: "anthropic"

# Default knowledge base settings
defaults:
  ingestion:
    chunking:
      strategy: "fixed"
      chunk_size: 512
      chunk_overlap: 50
    parsing:
      engine: "auto"
      ocr_enabled: false
      
  retrieval:
    architecture: "semantic"
    top_k: 5
    similarity_threshold: 0.3
    
  agents:
    mode: "default"
    query_analyzer:
      always_retrieve: false
    response_generator:
      cite_sources: true

# Storage paths
storage:
  base_path: "~/.ragkit"
  database: "~/.ragkit/ragkit.db"
  vectors: "~/.ragkit/vectors"
  models: "~/.ragkit/models"
  logs: "~/.ragkit/logs"
```

#### 5.2 Knowledge Base Configuration

Chaque knowledge base a sa propre configuration :

```yaml
# ~/.ragkit/knowledge_bases/{kb_id}/config.yaml

name: "Documentation Projet X"
description: "Base de connaissances pour le projet X"

sources:
  - type: "local"
    path: "/Users/me/Documents/ProjectX"
    patterns: ["*.pdf", "*.md", "*.docx"]
    recursive: true
    
  - type: "local"
    path: "/Users/me/Notes"
    patterns: ["*.md"]

# Override global settings
providers:
  embedding:
    provider: "onnx_local"  # or inherit from global
  llm:
    provider: "ollama"
    model: "mistral:7b"  # Different model for this KB

ingestion:
  chunking:
    strategy: "semantic"
    similarity_threshold: 0.85
    
retrieval:
  architecture: "hybrid"
  semantic:
    weight: 0.6
  lexical:
    weight: 0.4
```

---

### 6. API Desktop Étendue

#### 6.1 Nouveaux endpoints

```python
# ragkit/api/routes/desktop.py

"""Desktop-specific API routes."""

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

router = APIRouter(prefix="/desktop")


# Knowledge Base Management
class CreateKBRequest(BaseModel):
    name: str
    description: str | None = None
    sources: list[dict]
    config: dict | None = None


@router.post("/knowledge-bases")
async def create_knowledge_base(request: CreateKBRequest):
    """Create a new knowledge base."""
    pass


@router.get("/knowledge-bases")
async def list_knowledge_bases():
    """List all knowledge bases."""
    pass


@router.delete("/knowledge-bases/{kb_id}")
async def delete_knowledge_base(kb_id: str):
    """Delete a knowledge base and its data."""
    pass


# Ingestion with progress
@router.post("/knowledge-bases/{kb_id}/ingest")
async def start_ingestion(
    kb_id: str, 
    background_tasks: BackgroundTasks
):
    """Start document ingestion (async with progress)."""
    pass


@router.get("/knowledge-bases/{kb_id}/ingest/status")
async def get_ingestion_status(kb_id: str):
    """Get current ingestion status."""
    pass


# Provider Management
@router.get("/providers/status")
async def get_providers_status():
    """Get status of all providers (Ollama, APIs)."""
    return {
        "ollama": {
            "installed": True,
            "running": True,
            "version": "0.3.12",
            "models": ["llama3.2:3b", "mistral:7b"],
        },
        "onnx": {
            "available": True,
            "models_downloaded": ["all-MiniLM-L6-v2"],
        },
        "openai": {
            "configured": True,
            "valid": True,
        },
    }


@router.post("/providers/ollama/pull")
async def pull_ollama_model(model_name: str, background_tasks: BackgroundTasks):
    """Download an Ollama model."""
    pass


@router.post("/providers/onnx/download")
async def download_onnx_model(model_name: str, background_tasks: BackgroundTasks):
    """Download an ONNX embedding model."""
    pass


@router.post("/providers/test")
async def test_provider(provider_config: dict):
    """Test a provider configuration."""
    pass


# Conversations
@router.get("/knowledge-bases/{kb_id}/conversations")
async def list_conversations(kb_id: str):
    """List conversations for a knowledge base."""
    pass


@router.post("/knowledge-bases/{kb_id}/conversations")
async def create_conversation(kb_id: str):
    """Create a new conversation."""
    pass


@router.get("/conversations/{conv_id}/messages")
async def get_messages(conv_id: str):
    """Get messages in a conversation."""
    pass
```

---

### 7. Mode Serveur Multi-utilisateurs

#### 7.1 Architecture Serveur

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       RAGKIT SERVER MODE                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                         Load Balancer                               │ │
│  │                    (nginx / cloud LB)                               │ │
│  └─────────────────────────────┬──────────────────────────────────────┘ │
│                                │                                         │
│  ┌─────────────────────────────▼──────────────────────────────────────┐ │
│  │                      RAGKIT API Cluster                             │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                         │ │
│  │  │ Instance │  │ Instance │  │ Instance │  (stateless)            │ │
│  │  │    1     │  │    2     │  │    N     │                         │ │
│  │  └──────────┘  └──────────┘  └──────────┘                         │ │
│  └─────────────────────────────┬──────────────────────────────────────┘ │
│                                │                                         │
│  ┌─────────────────────────────▼──────────────────────────────────────┐ │
│  │                        Shared Services                              │ │
│  │                                                                      │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │ │
│  │  │  PostgreSQL  │  │    Qdrant    │  │    Redis                 │ │ │
│  │  │  (metadata)  │  │   (vectors)  │  │  (cache, sessions)       │ │ │
│  │  └──────────────┘  └──────────────┘  └──────────────────────────┘ │ │
│  │                                                                      │ │
│  │  ┌──────────────────────────────────────────────────────────────┐  │ │
│  │  │                    Object Storage (S3)                        │  │ │
│  │  │               (documents, models, exports)                    │  │ │
│  │  └──────────────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                        Auth & Multi-tenancy                         │ │
│  │                                                                      │ │
│  │  Users → Organizations → Knowledge Bases                            │ │
│  │                                                                      │ │
│  │  Roles: admin | editor | viewer                                     │ │
│  │  Auth: Local | OIDC | LDAP | SAML                                  │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 7.2 Configuration Serveur

```yaml
# ragkit-server.yaml

version: "2.0"

app:
  mode: "server"
  
server:
  host: "0.0.0.0"
  port: 8000
  workers: 4
  
auth:
  enabled: true
  provider: "local"  # local | oidc | ldap
  
  # Local auth
  local:
    jwt_secret_env: "JWT_SECRET"
    token_expiry: 3600
    
  # OIDC (for SSO)
  oidc:
    issuer: "https://auth.company.com"
    client_id_env: "OIDC_CLIENT_ID"
    client_secret_env: "OIDC_CLIENT_SECRET"

database:
  type: "postgresql"
  url_env: "DATABASE_URL"
  pool_size: 10

vector_store:
  provider: "qdrant"
  qdrant:
    mode: "cloud"
    url_env: "QDRANT_URL"
    api_key_env: "QDRANT_API_KEY"

cache:
  provider: "redis"
  url_env: "REDIS_URL"

storage:
  type: "s3"
  bucket_env: "S3_BUCKET"
  region_env: "AWS_REGION"

# Provider configuration (shared or per-organization)
providers:
  embedding:
    default: "openai"
    allow_user_keys: true
    
  llm:
    default: "openai"
    allow_user_keys: true
```

#### 7.3 Modèle de données Multi-tenant

```python
# ragkit/storage/models/server.py

"""Server mode data models with multi-tenancy."""

from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from ragkit.storage.database import Base


class UserRole(str, Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    users = relationship("OrganizationUser", back_populates="organization")
    knowledge_bases = relationship("KnowledgeBase", back_populates="organization")


class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    email = Column(String, unique=True, nullable=False)
    name = Column(String)
    hashed_password = Column(String)  # null for SSO users
    provider = Column(String, default="local")  # local | oidc | ldap
    created_at = Column(DateTime, default=datetime.utcnow)
    
    organizations = relationship("OrganizationUser", back_populates="user")


class OrganizationUser(Base):
    __tablename__ = "organization_users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"))
    user_id = Column(String, ForeignKey("users.id"))
    role = Column(SQLEnum(UserRole), default=UserRole.VIEWER)
    
    organization = relationship("Organization", back_populates="users")
    user = relationship("User", back_populates="organizations")


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"))
    name = Column(String, nullable=False)
    description = Column(Text)
    config = Column(Text)  # JSON
    is_public = Column(String, default=False)  # Public chatbot access
    created_at = Column(DateTime, default=datetime.utcnow)
    
    organization = relationship("Organization", back_populates="knowledge_bases")
```

---

## 🔐 Sécurité

### Stockage des clés API

```python
# ragkit/security/keyring.py

"""Secure API key storage using system keyring."""

import keyring
from cryptography.fernet import Fernet


class SecureKeyStore:
    """Store API keys securely using OS keyring."""
    
    SERVICE_NAME = "ragkit"
    
    def __init__(self):
        self._ensure_encryption_key()
    
    def _ensure_encryption_key(self):
        """Ensure encryption key exists in keyring."""
        key = keyring.get_password(self.SERVICE_NAME, "encryption_key")
        if not key:
            key = Fernet.generate_key().decode()
            keyring.set_password(self.SERVICE_NAME, "encryption_key", key)
        self._fernet = Fernet(key.encode())
    
    def store_api_key(self, provider: str, api_key: str) -> None:
        """Store an API key securely."""
        encrypted = self._fernet.encrypt(api_key.encode()).decode()
        keyring.set_password(self.SERVICE_NAME, f"api_key_{provider}", encrypted)
    
    def get_api_key(self, provider: str) -> str | None:
        """Retrieve an API key."""
        encrypted = keyring.get_password(self.SERVICE_NAME, f"api_key_{provider}")
        if encrypted:
            return self._fernet.decrypt(encrypted.encode()).decode()
        return None
    
    def delete_api_key(self, provider: str) -> None:
        """Delete an API key."""
        keyring.delete_password(self.SERVICE_NAME, f"api_key_{provider}")
    
    def list_providers(self) -> list[str]:
        """List providers with stored keys."""
        # Implementation depends on keyring backend
        pass
```

---

## 📊 Métriques et Telemetry

### Métriques locales (opt-in)

```python
# ragkit/observability/metrics.py

"""Local metrics collection."""

from datetime import datetime
from pathlib import Path
import json


class LocalMetrics:
    """Collect usage metrics locally."""
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path / "metrics.jsonl"
    
    def track(self, event: str, properties: dict | None = None):
        """Track an event locally."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            "properties": properties or {},
        }
        
        with open(self.storage_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    def get_summary(self) -> dict:
        """Get usage summary."""
        # Parse metrics file and return summary
        pass
```

---

## 📱 Distribution

### Packaging

| Plateforme | Format | Outil | Taille estimée |
|------------|--------|-------|----------------|
| macOS | .dmg | Tauri | ~50 MB (sans modèles) |
| Windows | .msi | Tauri | ~50 MB (sans modèles) |
| Linux | .AppImage / .deb | Tauri | ~50 MB (sans modèles) |

### Auto-update

```yaml
# tauri.conf.json (extrait)
{
  "tauri": {
    "updater": {
      "active": true,
      "endpoints": [
        "https://releases.ragkit.io/{{target}}/{{current_version}}"
      ],
      "dialog": true,
      "pubkey": "..."
    }
  }
}
```

---

## 📚 Annexes

### A. Dépendances Python (Desktop)

```toml
# pyproject.toml additions

[project.optional-dependencies]
desktop = [
    "onnxruntime>=1.16",
    "tokenizers>=0.15",
    "keyring>=24.0",
    "httpx>=0.25",
]

server = [
    "sqlalchemy>=2.0",
    "asyncpg>=0.29",
    "redis>=5.0",
    "python-jose[cryptography]>=3.3",
    "passlib[bcrypt]>=1.7",
]
```

### B. Variables d'environnement

| Variable | Description | Mode |
|----------|-------------|------|
| `RAGKIT_DATA_DIR` | Chemin données utilisateur | Desktop |
| `RAGKIT_LOG_LEVEL` | Niveau de log | Tous |
| `OPENAI_API_KEY` | Clé API OpenAI | Tous |
| `ANTHROPIC_API_KEY` | Clé API Anthropic | Tous |
| `COHERE_API_KEY` | Clé API Cohere | Tous |
| `DATABASE_URL` | URL PostgreSQL | Server |
| `REDIS_URL` | URL Redis | Server |
| `JWT_SECRET` | Secret JWT | Server |

---

## 🔗 Documents Liés

- [RAGKIT_DESKTOP_ROADMAP.md](./RAGKIT_DESKTOP_ROADMAP.md) - Planning d'implémentation
- [CONTEXT.md](./CONTEXT.md) - Contexte projet original
- [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) - Plan V1 (complété)
