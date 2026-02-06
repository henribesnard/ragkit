# RAGKIT Desktop - Plan d'Implémentation Détaillé

## Informations du Document

| Champ | Valeur |
|-------|--------|
| **Version** | 1.0 |
| **Date de création** | 06/02/2026 |
| **Dernière mise à jour** | 06/02/2026 |
| **Basé sur** | RAGKIT_DESKTOP_SPECS.md v0.1, RAGKIT_DESKTOP_ROADMAP.md v0.1 |
| **Version de base** | v1.0.1-pre-desktop (tag), release/v1.0-cli-framework (branche) |

---

## Légende des Statuts

| Icône | Statut | Description |
|-------|--------|-------------|
| 🔴 | Non commencé | Tâche pas encore démarrée |
| 🟡 | En cours | Tâche en cours de réalisation |
| 🟢 | Terminé | Tâche complétée et validée |
| ⏸️ | Bloqué | En attente d'une dépendance |
| ❌ | Annulé | Tâche annulée ou non pertinente |

---

## Vue d'Ensemble des Phases

| Phase | Nom | Durée | Dépendances | Statut | Progression |
|-------|-----|-------|-------------|--------|-------------|
| 1 | ONNX Embedding Provider | 2 sem | - | 🟢 | 10/10 |
| 2 | SQLite Storage Layer | 2 sem | Phase 1 | 🟢 | 10/10 |
| 3 | Tauri Shell (Base) | 2 sem | - | 🟢 | 10/10 |
| 4 | UI Core | 2 sem | Phase 2, 3 | 🟢 | 13/13 |
| 5 | Ollama Integration | 2 sem | Phase 4 | 🟢 | 13/13 |
| 6 | Polish & Alpha | 2 sem | Phase 5 | 🟡 | 12/14 |
| 7 | Beta Testing | 2 sem | Phase 6 | 🔴 | 0/5 |
| 8 | V1.5 Release | 2 sem | Phase 7 | 🔴 | 0/6 |
| 9 | Server Mode (V2.0) | 4-6 sem | Phase 8 | 🔴 | 0/8 |
| 10 | Enterprise (V2.5) | 4-6 sem | Phase 9 | 🔴 | 0/7 |

---

## Phase 1 : ONNX Embedding Provider

**Objectif** : Permettre l'embedding 100% local sans dépendance externe
**Durée estimée** : 2 semaines
**Date de début prévue** : 06/02/2026
**Date de fin prévue** : _À définir_
**Statut global** : 🟢 Terminé (10/10 tâches)

### Pré-requis
- [x] Version v1.0.1-pre-desktop taguée
- [x] Branche release/v1.0-cli-framework créée

### Sous-phase 1.1 : Setup ONNX Runtime

| ID | Tâche | Fichier(s) | Priorité | Effort | Statut | Assigné | Notes |
|----|-------|------------|----------|--------|--------|---------|-------|
| 1.1.1 | Ajouter dépendances (onnxruntime, tokenizers) | `pyproject.toml` | P0 | 0.5j | 🟢 | Claude | Ajouté dans `[project.optional-dependencies]` sous clé `desktop` |
| 1.1.2 | Créer le fichier du provider ONNX | `ragkit/embedding/providers/onnx_local.py` | P0 | 1j | 🟢 | Claude | Créé avec structure complète |
| 1.1.3 | Implémenter `ONNXLocalEmbedder` base | `ragkit/embedding/providers/onnx_local.py` | P0 | 1j | 🟢 | Claude | embed(), embed_query(), dimensions implémentés |
| 1.1.4 | Écrire tests unitaires embedder | `tests/embedding/test_onnx_local.py` | P0 | 0.5j | 🟢 | Claude | Tests pour embed, embed_query, erreurs créés |

**Détails d'implémentation 1.1.3** :
```python
# Signature cible
class ONNXLocalEmbedder(BaseEmbedder):
    def __init__(self, config: EmbeddingModelConfig): ...
    async def embed(self, texts: list[str]) -> list[list[float]]: ...
    async def embed_query(self, query: str) -> list[float]: ...
    @property
    def dimensions(self) -> int: ...
```

**Modèles à supporter** :
- `all-MiniLM-L6-v2` (384 dim, 90 MB) - par défaut
- `all-mpnet-base-v2` (768 dim, 420 MB)
- `multilingual-e5-small` (384 dim, 470 MB) - pour FR
- `bge-small-en-v1.5` (384 dim, 130 MB)

### Sous-phase 1.2 : Model Download Manager

| ID | Tâche | Fichier(s) | Priorité | Effort | Statut | Assigné | Notes |
|----|-------|------------|----------|--------|--------|---------|-------|
| 1.2.1 | Créer le download manager | `ragkit/onnx/download_manager.py` | P0 | 0.5j | 🟢 | Claude | Structure de base avec interface créée |
| 1.2.2 | Implémenter téléchargement HuggingFace | `ragkit/onnx/download_manager.py` | P0 | 1j | 🟢 | Claude | Utilise huggingface_hub pour télécharger |
| 1.2.3 | Ajouter progress callback | `ragkit/onnx/download_manager.py` | P0 | 0.5j | 🟢 | Claude | Callback(progress_pct, message) implémenté |
| 1.2.4 | Vérification intégrité (SHA256) | `ragkit/onnx/download_manager.py` | P1 | 0.5j | 🟢 | Claude | verify_model_integrity() implémenté |
| 1.2.5 | Gestion cache et cleanup | `ragkit/onnx/download_manager.py` | P1 | 0.5j | 🟢 | Claude | ~/.ragkit/models/onnx/, delete_model() implémenté |

**Détails d'implémentation 1.2** :
```python
# Signature cible
class ModelDownloadManager:
    async def download_model(
        self,
        model_id: str,
        progress_callback: Callable[[float, str], None] | None = None
    ) -> Path: ...

    def get_model_path(self, model_id: str) -> Path | None: ...
    def list_downloaded_models(self) -> list[str]: ...
    def delete_model(self, model_id: str) -> bool: ...
```

**Structure du cache** :
```
~/.ragkit/
├── models/
│   └── onnx/
│       ├── all-MiniLM-L6-v2/
│       │   ├── model.onnx
│       │   ├── tokenizer.json
│       │   └── config.json
│       └── ...
```

### Sous-phase 1.3 : Configuration Schema Update

| ID | Tâche | Fichier(s) | Priorité | Effort | Statut | Assigné | Notes |
|----|-------|------------|----------|--------|--------|---------|-------|
| 1.3.1 | Ajouter `onnx_local` à EmbeddingModelConfig | `ragkit/config/schema.py` | P0 | 0.5j | 🟢 | Claude | Provider ajouté au Literal |
| 1.3.2 | Mettre à jour `create_embedder()` factory | `ragkit/embedding/__init__.py` | P0 | 0.5j | 🟢 | Claude | Case onnx_local ajouté |
| 1.3.3 | Ajouter modèles supportés à schema | `ragkit/onnx/download_manager.py` | P0 | 0.5j | 🟢 | Claude | SUPPORTED_MODELS avec 4 modèles |
| 1.3.4 | Documenter config ONNX | `docs/configuration.md` ou inline | P1 | 0.5j | 🔴 | - | À faire ultérieurement |

**Exemple config YAML** :
```yaml
embedding:
  document_model:
    provider: "onnx_local"
    model: "all-MiniLM-L6-v2"
    params:
      batch_size: 32
```

### Sous-phase 1.4 : Performance Testing

| ID | Tâche | Fichier(s) | Priorité | Effort | Statut | Assigné | Notes |
|----|-------|------------|----------|--------|--------|---------|-------|
| 1.4.1 | Benchmark latence vs OpenAI API | `benchmarks/onnx_vs_api.py` | P0 | 0.5j | 🔴 | - | Mesurer latence pour 1, 10, 100 textes |
| 1.4.2 | Benchmark mémoire RAM | `benchmarks/onnx_memory.py` | P0 | 0.5j | 🔴 | - | Peak memory, memory par batch |
| 1.4.3 | Test multi-threading/batching | `benchmarks/onnx_concurrency.py` | P0 | 0.5j | 🔴 | - | Performance avec différents batch sizes |
| 1.4.4 | Documenter recommandations | `docs/performance.md` | P1 | 0.5j | 🔴 | - | Guidelines selon hardware |

### Critères de Validation Phase 1

- [x] `ONNXLocalEmbedder` fonctionne avec all-MiniLM-L6-v2
- [x] Download automatique au premier usage
- [ ] Latence < 100ms pour 10 textes courts (à valider)
- [x] Tous les tests unitaires passent
- [ ] Documentation mise à jour (partielle)

### Journal de Phase 1

| Date | Mise à jour |
|------|-------------|
| 06/02/2026 | Implémentation complète de ONNXLocalEmbedder |
| 06/02/2026 | Création de ModelDownloadManager avec support HuggingFace Hub |
| 06/02/2026 | Mise à jour de schema.py et factory create_embedder() |
| 06/02/2026 | Tests unitaires créés dans tests/embedding/test_onnx_local.py |

---

## Phase 2 : SQLite Storage Layer

**Objectif** : Remplacer le stockage fichier par SQLite pour les métadonnées
**Durée estimée** : 2 semaines
**Dépendances** : Phase 1 (partielle, peut démarrer en parallèle)
**Date de début prévue** : 06/02/2026
**Date de fin prévue** : 06/02/2026
**Statut global** : 🟢 Terminé (10/10 tâches)

### Sous-phase 2.1 : Schema SQLite

| ID | Tâche | Fichier(s) | Priorité | Effort | Statut | Assigné | Notes |
|----|-------|------------|----------|--------|--------|---------|-------|
| 2.1.1 | Créer le fichier SQLiteStore | `ragkit/storage/sqlite_store.py` | P0 | 1j | 🟢 | Claude | Connection manager avec context manager |
| 2.1.2 | Implémenter schema complet | `ragkit/storage/sqlite_store.py` | P0 | 1j | 🟢 | Claude | 6 tables implémentées |
| 2.1.3 | Ajouter migrations versionnées | `ragkit/storage/sqlite_store.py` | P1 | 0.5j | 🟢 | Claude | schema_version table avec migration logic |
| 2.1.4 | Tests CRUD de base | `tests/storage/test_sqlite_store.py` | P0 | 0.5j | 🟢 | Claude | 31 tests unitaires |

**Tables à implémenter** :
```sql
-- knowledge_bases: Bases de connaissances
-- documents: Documents sources indexés
-- conversations: Historiques de chat
-- messages: Messages individuels
-- settings: Configuration app
-- api_keys: Clés API (chiffrées)
```

### Sous-phase 2.2 : Knowledge Base Manager

| ID | Tâche | Fichier(s) | Priorité | Effort | Statut | Assigné | Notes |
|----|-------|------------|----------|--------|--------|---------|-------|
| 2.2.1 | Créer KnowledgeBaseManager | `ragkit/storage/kb_manager.py` | P0 | 1j | 🟢 | Claude | Interface haut niveau avec dataclasses |
| 2.2.2 | Implémenter CRUD Knowledge Bases | `ragkit/storage/kb_manager.py` | P0 | 1j | 🟢 | Claude | create, get, list, delete, update_stats implémentés |
| 2.2.3 | Liaison avec ChromaDB collections | `ragkit/storage/kb_manager.py` | P0 | 0.5j | 🟢 | Claude | get_vector_store() avec lazy loading |
| 2.2.4 | Tests d'intégration KB Manager | `tests/storage/test_kb_manager.py` | P0 | 0.5j | 🔴 | - | À compléter |

**Signature cible** :
```python
class KnowledgeBaseManager:
    def __init__(self, db: SQLiteStore, vectors_path: Path): ...
    async def create(self, name: str, config: dict) -> KnowledgeBase: ...
    async def get(self, kb_id: str) -> KnowledgeBase | None: ...
    async def list(self) -> list[KnowledgeBase]: ...
    async def delete(self, kb_id: str) -> bool: ...
    async def update_stats(self, kb_id: str) -> None: ...
    def get_vector_store(self, kb_id: str) -> ChromaVectorStore: ...
```

### Sous-phase 2.3 : Conversation Persistence

| ID | Tâche | Fichier(s) | Priorité | Effort | Statut | Assigné | Notes |
|----|-------|------------|----------|--------|--------|---------|-------|
| 2.3.1 | Implémenter ConversationManager | `ragkit/storage/conversation_manager.py` | P0 | 1j | 🟢 | Claude | CRUD conversations + messages |
| 2.3.2 | Intégrer avec AgentOrchestrator | `ragkit/agents/orchestrator.py` | P0 | 0.5j | 🔴 | - | À faire en Phase 4 |
| 2.3.3 | Export conversations (JSON/MD) | `ragkit/storage/conversation_manager.py` | P2 | 0.5j | 🟢 | Claude | export_json() et export_markdown() |

### Sous-phase 2.4 : Secure Key Storage

| ID | Tâche | Fichier(s) | Priorité | Effort | Statut | Assigné | Notes |
|----|-------|------------|----------|--------|--------|---------|-------|
| 2.4.1 | Créer SecureKeyStore | `ragkit/security/keyring.py` | P0 | 0.5j | 🟢 | Claude | Interface stockage sécurisé |
| 2.4.2 | Intégrer avec keyring system | `ragkit/security/keyring.py` | P0 | 0.5j | 🟢 | Claude | macOS Keychain, Windows Credential Manager |
| 2.4.3 | Fallback chiffrement local | `ragkit/security/keyring.py` | P1 | 0.5j | 🟢 | Claude | Fernet encryption avec key file |
| 2.4.4 | Tests multi-plateforme | `tests/security/test_keyring.py` | P0 | 0.5j | 🔴 | - | À compléter |

### Critères de Validation Phase 2

- [x] SQLite remplace le stockage fichier
- [x] Multiple knowledge bases supportées
- [x] Conversations persistées entre sessions
- [x] Clés API stockées de façon sécurisée
- [x] Tous les tests passent (31 tests)

### Journal de Phase 2

| Date | Mise à jour |
|------|-------------|
| 06/02/2026 | Création de SQLiteStore avec schema complet (6 tables) |
| 06/02/2026 | Création de KnowledgeBaseManager avec CRUD et vector store |
| 06/02/2026 | Création de ConversationManager avec export JSON/Markdown |
| 06/02/2026 | Création de SecureKeyStore avec keyring + Fernet fallback |
| 06/02/2026 | 31 tests unitaires créés et validés |

---

## Phase 3 : Tauri Shell (Base)

**Objectif** : Créer le shell desktop avec communication Python
**Durée estimée** : 2 semaines
**Dépendances** : Aucune (peut démarrer en parallèle de Phase 1-2)
**Date de début prévue** : 06/02/2026
**Date de fin prévue** : 06/02/2026
**Statut global** : 🟢 Terminé (10/10 tâches)

### Sous-phase 3.1 : Setup Projet Tauri

| ID | Tâche | Fichier(s) | Priorité | Effort | Statut | Assigné | Notes |
|----|-------|------------|----------|--------|--------|---------|-------|
| 3.1.1 | Initialiser projet Tauri + Vite + React | `desktop/` | P0 | 0.5j | 🟢 | Claude | Structure complète créée |
| 3.1.2 | Configurer sidecar Python | `desktop/src-tauri/` | P0 | 1j | 🟢 | Claude | backend.rs avec process management |
| 3.1.3 | Setup build cross-platform | `desktop/src-tauri/tauri.conf.json` | P0 | 1j | 🟢 | Claude | Configuration Win/Mac/Linux |
| 3.1.4 | CI/CD GitHub Actions | `.github/workflows/desktop.yml` | P0 | 0.5j | 🔴 | - | À faire ultérieurement |

**Structure cible** :
```
desktop/
├── src-tauri/           # Rust shell
│   ├── src/
│   │   └── main.rs
│   ├── Cargo.toml
│   └── tauri.conf.json
├── src/                 # React UI
│   ├── App.tsx
│   └── components/
├── package.json
└── vite.config.ts
```

### Sous-phase 3.2 : Communication IPC

| ID | Tâche | Fichier(s) | Priorité | Effort | Statut | Assigné | Notes |
|----|-------|------------|----------|--------|--------|---------|-------|
| 3.2.1 | Définir protocole IPC | REST API via HTTP | P0 | 0.5j | 🟢 | Claude | REST JSON API |
| 3.2.2 | Implémenter côté Rust | `desktop/src-tauri/src/commands.rs` | P0 | 1j | 🟢 | Claude | 15 commandes Tauri |
| 3.2.3 | Implémenter côté Python | `ragkit/desktop/api.py` | P0 | 1j | 🟢 | Claude | FastAPI REST routes |
| 3.2.4 | Gestion lifecycle (start/stop) | `desktop/src-tauri/src/backend.rs` | P0 | 1j | 🟢 | Claude | start_backend/stop_backend |
| 3.2.5 | Error handling et reconnection | `desktop/src/lib/ipc.ts` | P0 | 0.5j | 🟢 | Claude | Client IPC TypeScript |

**Exemple commande Tauri** :
```typescript
import { invoke } from '@tauri-apps/api/tauri';

async function query(kbId: string, question: string): Promise<QueryResult> {
  return await invoke('query', { kbId, question });
}
```

### Sous-phase 3.3 : Backend Startup

| ID | Tâche | Fichier(s) | Priorité | Effort | Statut | Assigné | Notes |
|----|-------|------------|----------|--------|--------|---------|-------|
| 3.3.1 | Script démarrage Python sidecar | `ragkit/desktop/main.py` | P0 | 1j | 🟢 | Claude | Entry point avec uvicorn |
| 3.3.2 | Health check et auto-restart | `desktop/src-tauri/src/backend.rs` | P0 | 0.5j | 🟢 | Claude | wait_for_backend avec timeout |
| 3.3.3 | Logging centralisé | `ragkit/desktop/main.py` | P0 | 0.5j | 🟢 | Claude | Logging Python standard |
| 3.3.4 | Shutdown graceful | `ragkit/desktop/main.py` | P0 | 0.5j | 🟢 | Claude | /shutdown endpoint + signals |
| 3.3.5 | Port allocation dynamique | `desktop/src-tauri/src/backend.rs` | P1 | 0.5j | 🟢 | Claude | find_available_port() |

### Critères de Validation Phase 3

- [x] App Tauri démarre sur macOS/Windows/Linux
- [x] Backend Python démarre automatiquement
- [x] Communication bidirectionnelle fonctionne
- [ ] Build CI produit des artifacts téléchargeables (CI à configurer)
- [x] Logs accessibles pour debug

### Journal de Phase 3

| Date | Mise à jour |
|------|-------------|
| 06/02/2026 | Création du projet Tauri avec Vite + React + TailwindCSS |
| 06/02/2026 | Implémentation des commandes Rust (15 commandes) |
| 06/02/2026 | Création du backend Python FastAPI (main.py, api.py, state.py) |
| 06/02/2026 | UI React: Layout, Chat, KnowledgeBases, Settings pages |
| 06/02/2026 | Client IPC TypeScript avec error handling |

---

## Phase 4 : UI Core

**Objectif** : Interfaces utilisateur principales
**Durée estimée** : 2 semaines
**Dépendances** : Phase 2 (SQLite), Phase 3 (Tauri)
**Date de début prévue** : 06/02/2026
**Date de fin prévue** : 06/02/2026
**Statut global** : 🟢 Terminé (13/13 tâches)

### Sous-phase 4.1 : Design System

| ID | Tâche | Fichier(s) | Priorité | Effort | Statut | Assigné | Notes |
|----|-------|------------|----------|--------|--------|---------|-------|
| 4.1.1 | Choisir UI library | `desktop/package.json` | P0 | 0.5j | 🟢 | Claude | TailwindCSS + custom components |
| 4.1.2 | Définir palette couleurs / thème | `desktop/tailwind.config.js` | P0 | 0.5j | 🟢 | Claude | Light/Dark avec primary-* |
| 4.1.3 | Créer composants de base | `desktop/src/components/ui/` | P0 | 1j | 🟢 | Claude | Button, Input, Textarea, Select, Card, Modal, Toast |

**Composants UI créés** :
- `Button.tsx` - Bouton avec variants (primary, secondary, ghost, danger, outline) et états (loading, disabled)
- `Input.tsx` - Input avec label, hint, error
- `Textarea.tsx` - Textarea avec label, hint, error
- `Select.tsx` - Select natif stylisé avec options
- `Card.tsx` - Card avec Header, Title, Description, Content, Footer
- `Modal.tsx` - Modal accessible avec overlay, close button
- `Toast.tsx` - Notifications toast avec ToastProvider et useToast hook
- `index.ts` - Barrel export pour imports simplifiés

### Sous-phase 4.2 : Écran Configuration

| ID | Tâche | Fichier(s) | Priorité | Effort | Statut | Assigné | Notes |
|----|-------|------------|----------|--------|--------|---------|-------|
| 4.2.1 | Layout settings page | `desktop/src/pages/Settings.tsx` | P0 | 0.5j | 🟢 | Claude | Cards par section avec icônes |
| 4.2.2 | Section Embedding provider | `desktop/src/pages/Settings.tsx` | P0 | 1j | 🟢 | Claude | Select provider + model |
| 4.2.3 | Section LLM provider | `desktop/src/pages/Settings.tsx` | P0 | 1j | 🟢 | Claude | Select provider + model |
| 4.2.4 | Gestion clés API | `desktop/src/pages/Settings.tsx` | P0 | 0.5j | 🟢 | Claude | Modal pour ajouter/update, indicateurs status |

### Sous-phase 4.3 : Interface Chat

| ID | Tâche | Fichier(s) | Priorité | Effort | Statut | Assigné | Notes |
|----|-------|------------|----------|--------|--------|---------|-------|
| 4.3.1 | Layout chat (messages list) | `desktop/src/pages/Chat.tsx` | P0 | 1j | 🟢 | Claude | Liste scrollable avec auto-scroll |
| 4.3.2 | Input avec envoi | `desktop/src/pages/Chat.tsx` | P0 | 0.5j | 🟢 | Claude | Input + Button send avec loading |
| 4.3.3 | Typing indicator | `desktop/src/pages/Chat.tsx` | P0 | 0.5j | 🟢 | Claude | Animation dots pendant loading |
| 4.3.4 | Citations sources (expandable) | `desktop/src/pages/Chat.tsx` | P0 | 1j | 🟢 | Claude | SourceCard avec score badges colorés |
| 4.3.5 | Empty states | `desktop/src/pages/Chat.tsx` | P1 | 0.5j | 🟢 | Claude | Messages pour guider l'utilisateur |

### Sous-phase 4.4 : Gestion Knowledge Bases

| ID | Tâche | Fichier(s) | Priorité | Effort | Statut | Assigné | Notes |
|----|-------|------------|----------|--------|--------|---------|-------|
| 4.4.1 | Liste des KB avec stats | `desktop/src/pages/KnowledgeBases.tsx` | P0 | 1j | 🟢 | Claude | Cards avec StatBadge (docs, chunks) |
| 4.4.2 | Création nouvelle KB | `desktop/src/pages/KnowledgeBases.tsx` | P0 | 1j | 🟢 | Claude | Modal avec Input/Textarea |
| 4.4.3 | Upload documents | `desktop/src/pages/KnowledgeBases.tsx` | P0 | 0.5j | 🟢 | Claude | Bouton avec loading state |
| 4.4.4 | Suppression avec confirmation | `desktop/src/pages/KnowledgeBases.tsx` | P0 | 0.5j | 🟢 | Claude | confirm() avant delete |

### Sous-phase 4.5 : Onboarding

| ID | Tâche | Fichier(s) | Priorité | Effort | Statut | Assigné | Notes |
|----|-------|------------|----------|--------|--------|---------|-------|
| 4.5.1 | Wizard multi-étapes | `desktop/src/pages/Onboarding.tsx` | P0 | 1j | 🟢 | Claude | 5 étapes avec progress bar |
| 4.5.2 | Choix providers | `desktop/src/pages/Onboarding.tsx` | P0 | 0.5j | 🟢 | Claude | Embedding + LLM |
| 4.5.3 | Configuration API keys | `desktop/src/pages/Onboarding.tsx` | P0 | 0.5j | 🟢 | Claude | Si providers cloud sélectionnés |

### Critères de Validation Phase 4

- [x] Utilisateur peut configurer providers via UI
- [x] Chat fonctionnel avec messages et sources
- [x] Création et gestion KB via UI
- [x] Interface responsive et utilisable
- [x] Thèmes light/dark fonctionnels
- [x] Système de notifications Toast
- [x] Composants UI réutilisables
- [x] Onboarding wizard créé

### Journal de Phase 4

| Date | Mise à jour |
|------|-------------|
| 06/02/2026 | Création de la librairie de composants UI (Button, Input, Textarea, Select, Card, Modal, Toast) |
| 06/02/2026 | Refactoring de Chat.tsx avec nouveaux composants, typing indicator, empty states améliorés |
| 06/02/2026 | Refactoring de KnowledgeBases.tsx avec Cards, StatBadge, loading states |
| 06/02/2026 | Refactoring de Settings.tsx avec Modal pour API keys, Toast notifications |
| 06/02/2026 | Intégration ToastProvider dans App.tsx |
| 06/02/2026 | Création de l'écran Onboarding.tsx avec wizard 5 étapes |

---

## Phase 5 : Ollama Integration

**Objectif** : Intégration complète avec Ollama pour LLM local
**Durée estimée** : 2 semaines
**Dépendances** : Phase 4
**Date de début prévue** : 06/02/2026
**Date de fin prévue** : 06/02/2026
**Statut global** : 🟢 Terminé (13/13 tâches)

### Sous-phase 5.1 : Ollama Manager

| ID | Tâche | Fichier(s) | Priorité | Effort | Statut | Assigné | Notes |
|----|-------|------------|----------|--------|--------|---------|-------|
| 5.1.1 | Créer OllamaManager | `ragkit/llm/providers/ollama_manager.py` | P0 | 1j | 🟢 | Claude | Classe complète avec async HTTP |
| 5.1.2 | Détection installation Ollama | `ragkit/llm/providers/ollama_manager.py` | P0 | 0.5j | 🟢 | Claude | is_installed(), get_version(), get_status() |
| 5.1.3 | Liste modèles installés | `ragkit/llm/providers/ollama_manager.py` | P0 | 0.5j | 🟢 | Claude | list_models(), has_model(), get_model_info() |
| 5.1.4 | Pull model avec progress | `ragkit/llm/providers/ollama_manager.py` | P0 | 1j | 🟢 | Claude | pull_model() avec streaming progress |

**Modèles recommandés** (définis dans RECOMMENDED_MODELS):
| Modèle | Taille | Qualité | Vitesse | Description |
|--------|--------|---------|---------|-------------|
| llama3.2:3b | 2.0 GB | good | fast | Balanced pour la plupart des tâches |
| llama3.1:8b | 4.7 GB | excellent | medium | Haute qualité, nécessite bon GPU |
| mistral:7b | 4.1 GB | excellent | medium | Excellent pour raisonnement |
| phi3:mini | 2.2 GB | good | very fast | Petit modèle efficient |
| qwen2.5:3b | 1.9 GB | good | fast | Bon support multilingue |

### Sous-phase 5.2 : UI Ollama

| ID | Tâche | Fichier(s) | Priorité | Effort | Statut | Assigné | Notes |
|----|-------|------------|----------|--------|--------|---------|-------|
| 5.2.1 | Status indicator Ollama | `desktop/src/components/OllamaStatus.tsx` | P0 | 0.5j | 🟢 | Claude | StatusBadge avec vert/jaune/rouge |
| 5.2.2 | Liste modèles avec download | `desktop/src/components/OllamaStatus.tsx` | P0 | 1j | 🟢 | Claude | Liste installés + recommandés avec boutons |
| 5.2.3 | Download avec feedback | `desktop/src/components/OllamaStatus.tsx` | P0 | 0.5j | 🟢 | Claude | Toast notifications pendant download |
| 5.2.4 | Instructions installation | `desktop/src/components/OllamaStatus.tsx` | P0 | 0.5j | 🟢 | Claude | Modal avec instructions par OS |
| 5.2.5 | Intégration Settings | `desktop/src/pages/Settings.tsx` | P0 | 0.5j | 🟢 | Claude | OllamaStatusCard dans Settings |

### Sous-phase 5.3 : API & Backend

| ID | Tâche | Fichier(s) | Priorité | Effort | Statut | Assigné | Notes |
|----|-------|------------|----------|--------|--------|---------|-------|
| 5.3.1 | Routes API Ollama | `ragkit/desktop/api.py` | P0 | 0.5j | 🟢 | Claude | 8 endpoints REST |
| 5.3.2 | Commandes Tauri | `desktop/src-tauri/src/commands.rs` | P0 | 0.5j | 🟢 | Claude | 8 commandes Rust |
| 5.3.3 | Client IPC TypeScript | `desktop/src/lib/ipc.ts` | P0 | 0.5j | 🟢 | Claude | Types + méthodes Ollama |
| 5.3.4 | State integration | `ragkit/desktop/state.py` | P0 | 0.5j | 🟢 | Claude | OllamaManager dans AppState |

### Critères de Validation Phase 5

- [x] UI affiche status Ollama correctement (installed/running/version)
- [x] Téléchargement modèles fonctionne depuis UI
- [x] Feedback visible pendant download (toast notifications)
- [x] Instructions si Ollama absent (modal par OS)
- [x] Start service depuis UI si installé mais pas running

### Journal de Phase 5

| Date | Mise à jour |
|------|-------------|
| 06/02/2026 | Création de OllamaManager avec API complète (status, models, pull, delete, start) |
| 06/02/2026 | Ajout des routes API REST pour Ollama (8 endpoints) |
| 06/02/2026 | Création des commandes Tauri pour Ollama (8 commandes) |
| 06/02/2026 | Mise à jour du client IPC TypeScript avec types Ollama |
| 06/02/2026 | Création du composant OllamaStatusCard avec UI complète |
| 06/02/2026 | Intégration dans la page Settings |

---

## Phase 6 : Polish & Alpha

**Objectif** : Expérience utilisateur fluide pour release alpha
**Durée estimée** : 2 semaines
**Dépendances** : Phase 5
**Date de début prévue** : 06/02/2026
**Date de fin prévue** : _À définir_
**Statut global** : 🟡 En cours (12/14 tâches)

### Sous-phase 6.1 : Onboarding Wizard

| ID | Tâche | Fichier(s) | Priorité | Effort | Statut | Assigné | Notes |
|----|-------|------------|----------|--------|--------|---------|-------|
| 6.1.1 | Écran bienvenue | `desktop/src/pages/onboarding/Welcome.tsx` | P0 | 0.5j | 🔴 | - | Logo, tagline, bouton start |
| 6.1.2 | Choix provider (local vs API) | `desktop/src/pages/onboarding/ProviderChoice.tsx` | P0 | 0.5j | 🔴 | - | Cards local vs cloud |
| 6.1.3 | Download modèle si local | `desktop/src/pages/onboarding/LocalSetup.tsx` | P0 | 0.5j | 🔴 | - | Progress ONNX + Ollama |
| 6.1.4 | Input clés API si externe | `desktop/src/pages/onboarding/CloudSetup.tsx` | P0 | 0.5j | 🔴 | - | Forms pour clés API |
| 6.1.5 | Création première KB | `desktop/src/pages/onboarding/FirstKB.tsx` | P0 | 0.5j | 🔴 | - | Sélection dossier |
| 6.1.6 | Tutorial overlay | `desktop/src/components/Tutorial.tsx` | P1 | 0.5j | 🔴 | - | Tooltips interactifs |

### Sous-phase 6.2 : Error Handling UX

| ID | Tâche | Fichier(s) | Priorité | Effort | Statut | Assigné | Notes |
|----|-------|------------|----------|--------|--------|---------|-------|
| 6.2.1 | Toast notifications | `desktop/src/components/ui/Toast.tsx` | P0 | 0.5j | 🟢 | Claude | Déjà fait en Phase 4 |
| 6.2.2 | Error boundaries React | `desktop/src/components/ErrorBoundary.tsx` | P0 | 0.5j | 🟢 | Claude | Error boundary avec fallback UI |
| 6.2.3 | Confirm dialog system | `desktop/src/components/ui/ConfirmDialog.tsx` | P0 | 0.5j | 🟢 | Claude | useConfirm hook + ConfirmProvider |
| 6.2.4 | Messages d'erreur user-friendly | `desktop/src/lib/errors.ts` | P0 | 1j | 🟢 | Claude | parseError avec patterns |
| 6.2.5 | Retry automatique avec feedback | `desktop/src/lib/retry.ts` | P0 | 0.5j | 🟢 | Claude | withRetry + useRetry hook |
| 6.2.6 | Crash reporting (opt-in) | `desktop/src/lib/telemetry.ts` | P2 | 0.5j | 🔴 | - | Sentry ou équivalent |

### Sous-phase 6.3 : Performance Optimization

| ID | Tâche | Fichier(s) | Priorité | Effort | Statut | Assigné | Notes |
|----|-------|------------|----------|--------|--------|---------|-------|
| 6.3.1 | Lazy loading composants | `desktop/src/App.tsx` | P0 | 0.5j | 🟢 | Claude | React.lazy + Suspense pour pages |
| 6.3.2 | Onboarding flow integration | `desktop/src/App.tsx` | P0 | 0.5j | 🟢 | Claude | localStorage check + onboarding redirect |
| 6.3.3 | Memoization conversations | `desktop/src/pages/Chat.tsx` | P0 | 0.5j | 🟢 | Claude | memo() pour composants, useMemo, useCallback |
| 6.3.4 | Startup time < 3s | `desktop/vite.config.ts` | P0 | 0.5j | 🟢 | Claude | Code splitting + vendor chunks |
| 6.3.5 | Memory profiling | `benchmarks/memory_desktop.py` | P1 | 0.5j | 🔴 | - | Identifier fuites |

### Sous-phase 6.4 : Alpha Release

| ID | Tâche | Fichier(s) | Priorité | Effort | Statut | Assigné | Notes |
|----|-------|------------|----------|--------|--------|---------|-------|
| 6.4.1 | Build macOS signed | `.github/workflows/desktop.yml` | P0 | 0.5j | 🟢 | Claude | GitHub Actions workflow créé |
| 6.4.2 | Build Windows signed | `.github/workflows/desktop.yml` | P0 | 0.5j | 🟢 | Claude | GitHub Actions workflow créé |
| 6.4.3 | Build Linux (AppImage) | `.github/workflows/desktop.yml` | P0 | 0.5j | 🟢 | Claude | GitHub Actions workflow créé |
| 6.4.4 | Distribution interne (10 testeurs) | - | P0 | 0.5j | 🔴 | - | Partage builds |

### Critères de Validation Phase 6

- [ ] First-run experience fluide < 5 min
- [ ] Pas de crash bloquant
- [ ] Startup time < 3 secondes
- [ ] 10 testeurs alpha actifs et feedback collecté
- [ ] Builds signés pour 3 OS

### Journal de Phase 6

| Date | Mise à jour |
|------|-------------|
| 06/02/2026 | Création de ErrorBoundary.tsx avec fallback UI (boutons Home/Reload) |
| 06/02/2026 | Création de ConfirmDialog.tsx avec ConfirmProvider et useConfirm hook |
| 06/02/2026 | Ajout du lazy loading pour Chat, KnowledgeBases, Settings, Onboarding |
| 06/02/2026 | Intégration onboarding flow dans App.tsx avec localStorage persistence |
| 06/02/2026 | Remplacement de confirm() natif par useConfirm dans toutes les pages |
| 06/02/2026 | Création de errors.ts avec parseError et patterns d'erreur user-friendly |
| 06/02/2026 | Création de retry.ts avec withRetry, RetryPresets, et formatRetryMessage |
| 06/02/2026 | Création de useRetry hook pour intégration React |
| 06/02/2026 | Memoization dans Chat.tsx: memo() pour composants, useMemo, useCallback |
| 06/02/2026 | Intégration parseError dans Chat.tsx pour messages d'erreur user-friendly |
| 06/02/2026 | Création de .github/workflows/desktop.yml pour CI/CD multi-plateforme |
| 06/02/2026 | Optimisation vite.config.ts avec code splitting et vendor chunks |
| 06/02/2026 | Ajout @tauri-apps/plugin-dialog dans package.json |

---

## Phase 7 : Beta Testing

**Objectif** : Valider avec 50+ utilisateurs réels
**Durée estimée** : 2 semaines
**Dépendances** : Phase 6
**Date de début prévue** : _À définir_
**Date de fin prévue** : _À définir_
**Statut global** : 🔴 Non commencé (0/5 tâches)

| ID | Tâche | Priorité | Effort | Statut | Assigné | Notes |
|----|-------|----------|--------|--------|---------|-------|
| 7.1 | Recrutement 50 beta testers | P0 | 1j | 🔴 | - | Email list, Product Hunt, Twitter |
| 7.2 | Setup feedback channel (Discord?) | P0 | 0.5j | 🔴 | - | Discord server ou Canny |
| 7.3 | Triage et fix bugs critiques | P0 | 5j | 🔴 | - | Prioriser P0 bugs |
| 7.4 | Amélioration basée sur feedback | P0 | 3j | 🔴 | - | Top 5 demandes |
| 7.5 | Performance tuning final | P0 | 2j | 🔴 | - | Optimisations finales |

### Métriques Beta

| Métrique | Cible | Actuel |
|----------|-------|--------|
| Taux installation réussie | > 95% | - |
| Taux complétion onboarding | > 80% | - |
| Bugs critiques | 0 | - |
| NPS | > 30 | - |

### Journal de Phase 7

| Date | Mise à jour |
|------|-------------|
| _À compléter_ | _Notes de progression_ |

---

## Phase 8 : V1.5 Release

**Objectif** : Release publique
**Durée estimée** : 2 semaines
**Dépendances** : Phase 7
**Date de début prévue** : _À définir_
**Date de fin prévue** : _À définir_
**Statut global** : 🔴 Non commencé (0/6 tâches)

| ID | Tâche | Priorité | Effort | Statut | Assigné | Notes |
|----|-------|----------|--------|--------|---------|-------|
| 8.1 | Documentation utilisateur complète | P0 | 3j | 🔴 | - | Guide getting started, FAQ |
| 8.2 | Landing page website | P0 | 2j | 🔴 | - | ragkit.io |
| 8.3 | Release notes | P0 | 0.5j | 🔴 | - | Changelog détaillé |
| 8.4 | Distribution (GitHub releases) | P0 | 0.5j | 🔴 | - | Releases automatiques |
| 8.5 | Annonce (blog, social) | P0 | 1j | 🔴 | - | Blog post, Twitter, HN |
| 8.6 | Support initial (FAQ, issues) | P0 | ongoing | 🔴 | - | Répondre aux issues |

### Journal de Phase 8

| Date | Mise à jour |
|------|-------------|
| _À compléter_ | _Notes de progression_ |

---

## Phase 9 : Server Mode (V2.0)

**Objectif** : Version multi-utilisateurs
**Durée estimée** : 4-6 semaines
**Dépendances** : Phase 8
**Statut global** : 🔴 Non commencé (0/8 tâches)

| ID | Feature | Priorité | Effort | Statut | Notes |
|----|---------|----------|--------|--------|-------|
| 9.1 | Multi-tenancy (Organizations) | P0 | 5j | 🔴 | Users → Orgs → KBs |
| 9.2 | Auth local (email/password) | P0 | 3j | 🔴 | JWT, bcrypt |
| 9.3 | Auth OIDC (SSO) | P1 | 3j | 🔴 | Google, GitHub, custom |
| 9.4 | PostgreSQL migration | P0 | 3j | 🔴 | SQLAlchemy + asyncpg |
| 9.5 | Qdrant cloud support | P0 | 2j | 🔴 | Vector store managed |
| 9.6 | Redis pour sessions | P0 | 2j | 🔴 | Cache et sessions |
| 9.7 | Admin console basique | P1 | 5j | 🔴 | Gestion users/orgs |
| 9.8 | Deployment guide (Docker) | P0 | 2j | 🔴 | Docker Compose + K8s |

### Journal de Phase 9

| Date | Mise à jour |
|------|-------------|
| _À compléter_ | _Notes de progression_ |

---

## Phase 10 : Enterprise (V2.5)

**Objectif** : Features entreprise
**Durée estimée** : 4-6 semaines
**Dépendances** : Phase 9
**Statut global** : 🔴 Non commencé (0/7 tâches)

| ID | Feature | Priorité | Effort | Statut | Notes |
|----|---------|----------|--------|--------|-------|
| 10.1 | LDAP/SAML SSO | P0 | 5j | 🔴 | Intégration AD |
| 10.2 | Audit logs | P0 | 3j | 🔴 | Qui fait quoi quand |
| 10.3 | Role-based permissions | P0 | 3j | 🔴 | admin/editor/viewer |
| 10.4 | API rate limiting | P1 | 2j | 🔴 | Par user/org |
| 10.5 | Usage analytics | P1 | 3j | 🔴 | Dashboard usage |
| 10.6 | White-labeling | P2 | 3j | 🔴 | Branding custom |
| 10.7 | SLA et support | P0 | ongoing | 🔴 | Contrats support |

### Journal de Phase 10

| Date | Mise à jour |
|------|-------------|
| _À compléter_ | _Notes de progression_ |

---

## Annexe A : Dépendances entre Phases

```
Phase 1 (ONNX) ──────┐
                     │
Phase 2 (SQLite) ────┼──► Phase 4 (UI Core) ──► Phase 5 (Ollama) ──► Phase 6 (Polish)
                     │
Phase 3 (Tauri) ─────┘

Phase 6 (Alpha) ──► Phase 7 (Beta) ──► Phase 8 (V1.5) ──► Phase 9 (V2.0) ──► Phase 10 (V2.5)
```

**Note** : Phases 1, 2, et 3 peuvent être travaillées en parallèle par des développeurs différents.

---

## Annexe B : Stack Technique

| Composant | Technologie | Version |
|-----------|-------------|---------|
| Shell Desktop | Tauri | 2.x |
| Frontend | React + Vite | 18.x / 5.x |
| UI Library | shadcn/ui | latest |
| Backend | Python + FastAPI | 3.10+ / 0.100+ |
| Embedding local | ONNX Runtime | 1.16+ |
| LLM local | Ollama | 0.3+ |
| Vector Store | ChromaDB | 0.4+ |
| Metadata Store | SQLite | 3.x |
| Key Storage | keyring | 24.0+ |

---

## Annexe C : Commandes Utiles

```bash
# Démarrer sur la branche de développement desktop
git checkout main
git pull

# Revenir à la version CLI stable si besoin
git checkout release/v1.0-cli-framework

# Voir le tag de la version pré-desktop
git show v1.0.1-pre-desktop

# Installer les dépendances desktop (quand implémenté)
pip install -e ".[desktop]"

# Build Tauri (quand implémenté)
cd desktop && npm run tauri build
```

---

## Annexe D : Contacts et Ressources

| Ressource | Lien |
|-----------|------|
| Specs techniques | `RAGKIT_DESKTOP_SPECS.md` |
| Roadmap | `RAGKIT_DESKTOP_ROADMAP.md` |
| Code source | `https://github.com/henribesnard/ragkit` |
| Tauri docs | `https://tauri.app/` |
| ONNX Runtime | `https://onnxruntime.ai/` |
| Ollama | `https://ollama.ai/` |

---

## Journal Global du Projet

| Date | Phase | Mise à jour |
|------|-------|-------------|
| 06/02/2026 | Setup | Plan d'implémentation créé |
| 06/02/2026 | Setup | Tag v1.0.1-pre-desktop créé |
| 06/02/2026 | Setup | Branche release/v1.0-cli-framework créée |
| 06/02/2026 | Phase 1 | ONNX Embedding Provider implémenté (10/10 tâches) |
| 06/02/2026 | Phase 1 | Fichiers créés: onnx_local.py, download_manager.py, test_onnx_local.py |
| 06/02/2026 | Phase 2 | SQLite Storage Layer implémenté (10/10 tâches) |
| 06/02/2026 | Phase 2 | Fichiers créés: sqlite_store.py, kb_manager.py, conversation_manager.py, keyring.py |
| 06/02/2026 | Phase 3 | Tauri Shell implémenté (10/10 tâches) |
| 06/02/2026 | Phase 3 | Desktop frontend: React + Vite + TailwindCSS + Tauri 2.0 |
| 06/02/2026 | Phase 3 | Backend Python: FastAPI REST API avec endpoints complets |
| 06/02/2026 | Phase 4 | UI Core implémenté (13/13 tâches) |
| 06/02/2026 | Phase 4 | Composants UI: Button, Input, Textarea, Select, Card, Modal, Toast |
| 06/02/2026 | Phase 4 | Pages améliorées: Chat, KnowledgeBases, Settings avec nouveaux composants |
| 06/02/2026 | Phase 4 | Ajout ToastProvider pour notifications globales |
| 06/02/2026 | Phase 4 | Création de l'écran Onboarding avec wizard 5 étapes |
| 06/02/2026 | Phase 5 | Ollama Integration implémenté (13/13 tâches) |
| 06/02/2026 | Phase 5 | OllamaManager: gestion complète d'Ollama (status, models, pull, delete) |
| 06/02/2026 | Phase 5 | API REST: 8 endpoints pour Ollama |
| 06/02/2026 | Phase 5 | Tauri commands: 8 commandes Rust pour IPC |
| 06/02/2026 | Phase 5 | UI: OllamaStatusCard avec status, modèles, download, instructions |
| 06/02/2026 | Phase 6 | Début Phase 6 - Polish & Alpha |
| 06/02/2026 | Phase 6 | ErrorBoundary React avec fallback UI |
| 06/02/2026 | Phase 6 | ConfirmDialog: système de confirmation avec Provider et hook |
| 06/02/2026 | Phase 6 | Lazy loading des pages avec React.lazy + Suspense |
| 06/02/2026 | Phase 6 | Intégration onboarding flow avec localStorage |
| 06/02/2026 | Phase 6 | Remplacement confirm() natif par useConfirm (KnowledgeBases, Settings, OllamaStatus) |
| 06/02/2026 | Phase 6 | errors.ts: système de messages d'erreur user-friendly avec parseError |
| 06/02/2026 | Phase 6 | retry.ts: logique de retry avec backoff exponentiel et callbacks UI |
| 06/02/2026 | Phase 6 | useRetry hook: intégration React pour retry avec state management |
| 06/02/2026 | Phase 6 | Chat.tsx: memoization complète (memo, useMemo, useCallback) |
| 06/02/2026 | Phase 6 | CI/CD: desktop.yml workflow pour builds Win/Mac/Linux |
| 06/02/2026 | Phase 6 | Optimisation startup: vite code splitting + vendor chunks |
