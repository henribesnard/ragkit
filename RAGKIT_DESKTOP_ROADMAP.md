# RAGKIT Desktop - Roadmap d'Implémentation

## 📋 Informations du Document

| Champ | Valeur |
|-------|--------|
| **Version** | 0.1 |
| **Date** | 05/02/2026 |
| **Horizon** | 6 mois |
| **Statut** | Draft |

---

## 🎯 Objectifs Stratégiques

### Vision à 6 mois

```
V1.0 (Core)     V1.5 (Desktop)      V2.0 (Server)       V2.5 (Enterprise)
    │                │                    │                    │
    ▼                ▼                    ▼                    ▼
┌────────┐      ┌────────┐          ┌────────┐          ┌────────┐
│  CLI   │ ──▶  │Desktop │  ──▶     │ Multi- │  ──▶     │ Cloud  │
│Framework│      │  App   │          │ User   │          │ SaaS   │
└────────┘      └────────┘          └────────┘          └────────┘
   Done          Q1 2026            Q2 2026             Q3 2026
```

### Métriques de succès

| Milestone | Métrique | Cible |
|-----------|----------|-------|
| V1.5 Alpha | Installation sans erreur | 95% |
| V1.5 Beta | Temps setup < 5 min | 90% users |
| V1.5 Release | NPS | > 40 |
| V2.0 | Entreprises pilotes | 5 |

---

## 📅 Planning Global

```
2026
│
├── Février ────────────────────────────────────────────────────────────
│   │
│   ├── S1-S2: Phase 1 - ONNX Embedding Provider
│   │          • Intégration ONNX Runtime
│   │          • Download manager pour modèles
│   │          • Tests performance
│   │
│   └── S3-S4: Phase 2 - SQLite Storage Layer
│              • Schema SQLite
│              • Migration depuis mode fichiers
│              • API CRUD knowledge bases
│
├── Mars ───────────────────────────────────────────────────────────────
│   │
│   ├── S1-S2: Phase 3 - Tauri Shell (base)
│   │          • Setup projet Tauri
│   │          • Communication IPC Python
│   │          • Build pipeline CI/CD
│   │
│   └── S3-S4: Phase 4 - UI Core
│              • Écran configuration
│              • Interface chat
│              • Gestion knowledge bases
│
├── Avril ──────────────────────────────────────────────────────────────
│   │
│   ├── S1-S2: Phase 5 - Ollama Integration
│   │          • Détection et status Ollama
│   │          • Pull models depuis UI
│   │          • Fallback et error handling
│   │
│   └── S3-S4: Phase 6 - Polish & Alpha
│              • Onboarding wizard
│              • Error handling UX
│              • Alpha release interne
│
├── Mai ────────────────────────────────────────────────────────────────
│   │
│   ├── S1-S2: Phase 7 - Beta Testing
│   │          • Beta fermée (50 users)
│   │          • Bug fixes critiques
│   │          • Performance tuning
│   │
│   └── S3-S4: Phase 8 - V1.5 Release
│              • Documentation utilisateur
│              • Landing page
│              • Release publique
│
├── Juin-Juillet ───────────────────────────────────────────────────────
│   │
│   └── Phase 9 - Server Mode (V2.0)
│       • Multi-tenancy
│       • Auth (local + OIDC)
│       • PostgreSQL + Qdrant
│
└── Août+ ──────────────────────────────────────────────────────────────
    │
    └── Phase 10 - Enterprise (V2.5)
        • SSO (SAML/LDAP)
        • Audit logs
        • Admin console
```

---

## 🔧 Phase 1 : ONNX Embedding Provider

**Durée** : 2 semaines  
**Objectif** : Permettre l'embedding 100% local sans dépendance externe

### Tâches détaillées

#### 1.1 Setup ONNX Runtime (3 jours)

| Tâche | Priorité | Effort | Statut |
|-------|----------|--------|--------|
| Ajouter dépendances (onnxruntime, tokenizers) | P0 | 0.5j | 🔴 |
| Créer `ragkit/embedding/providers/onnx_local.py` | P0 | 1j | 🔴 |
| Implémenter `ONNXLocalEmbedder` base | P0 | 1j | 🔴 |
| Tests unitaires embedder | P0 | 0.5j | 🔴 |

```python
# Signature cible
class ONNXLocalEmbedder(BaseEmbedder):
    def __init__(self, config: EmbeddingModelConfig): ...
    async def embed(self, texts: list[str]) -> list[list[float]]: ...
    async def embed_query(self, query: str) -> list[float]: ...
    @property
    def dimensions(self) -> int: ...
```

#### 1.2 Model Download Manager (3 jours)

| Tâche | Priorité | Effort | Statut |
|-------|----------|--------|--------|
| Créer `ragkit/models/download_manager.py` | P0 | 0.5j | 🔴 |
| Implémenter téléchargement HuggingFace | P0 | 1j | 🔴 |
| Ajouter progress callback | P0 | 0.5j | 🔴 |
| Vérification intégrité (SHA256) | P1 | 0.5j | 🔴 |
| Gestion cache et cleanup | P1 | 0.5j | 🔴 |

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

#### 1.3 Configuration Schema Update (2 jours)

| Tâche | Priorité | Effort | Statut |
|-------|----------|--------|--------|
| Ajouter `onnx_local` à EmbeddingModelConfig | P0 | 0.5j | 🔴 |
| Mettre à jour `create_embedder()` factory | P0 | 0.5j | 🔴 |
| Ajouter modèles supportés à schema | P0 | 0.5j | 🔴 |
| Documentation config ONNX | P1 | 0.5j | 🔴 |

```yaml
# Nouvelle config supportée
embedding:
  document_model:
    provider: "onnx_local"
    model: "all-MiniLM-L6-v2"
    params:
      batch_size: 32
```

#### 1.4 Performance Testing (2 jours)

| Tâche | Priorité | Effort | Statut |
|-------|----------|--------|--------|
| Benchmark vs OpenAI API (latence) | P0 | 0.5j | 🔴 |
| Benchmark mémoire RAM | P0 | 0.5j | 🔴 |
| Test multi-threading/batching | P0 | 0.5j | 🔴 |
| Documenter recommandations | P1 | 0.5j | 🔴 |

**Critères de succès Phase 1 :**
- [ ] `ONNXLocalEmbedder` fonctionne avec all-MiniLM-L6-v2
- [ ] Download automatique au premier usage
- [ ] Latence < 100ms pour 10 textes courts
- [ ] Tests unitaires passent

---

## 🗄️ Phase 2 : SQLite Storage Layer

**Durée** : 2 semaines  
**Objectif** : Remplacer le stockage fichier par SQLite pour les métadonnées

### Tâches détaillées

#### 2.1 Schema SQLite (3 jours)

| Tâche | Priorité | Effort | Statut |
|-------|----------|--------|--------|
| Créer `ragkit/storage/sqlite_store.py` | P0 | 1j | 🔴 |
| Implémenter schema (voir specs) | P0 | 1j | 🔴 |
| Ajouter migrations versionnées | P1 | 0.5j | 🔴 |
| Tests CRUD de base | P0 | 0.5j | 🔴 |

**Tables principales :**
- `knowledge_bases` - Bases de connaissances
- `documents` - Documents sources
- `conversations` - Historiques de chat
- `messages` - Messages individuels
- `settings` - Configuration app
- `api_keys` - Clés API (chiffrées)

#### 2.2 Knowledge Base Manager (3 jours)

| Tâche | Priorité | Effort | Statut |
|-------|----------|--------|--------|
| Créer `ragkit/storage/kb_manager.py` | P0 | 1j | 🔴 |
| CRUD Knowledge Bases | P0 | 1j | 🔴 |
| Liaison avec ChromaDB collections | P0 | 0.5j | 🔴 |
| Tests d'intégration | P0 | 0.5j | 🔴 |

```python
# Signature cible
class KnowledgeBaseManager:
    def __init__(self, db: SQLiteStore, vectors_path: Path): ...
    
    async def create(self, name: str, config: dict) -> KnowledgeBase: ...
    async def get(self, kb_id: str) -> KnowledgeBase | None: ...
    async def list(self) -> list[KnowledgeBase]: ...
    async def delete(self, kb_id: str) -> bool: ...
    async def update_stats(self, kb_id: str) -> None: ...
    
    def get_vector_store(self, kb_id: str) -> ChromaVectorStore: ...
```

#### 2.3 Conversation Persistence (2 jours)

| Tâche | Priorité | Effort | Statut |
|-------|----------|--------|--------|
| Implémenter `ConversationManager` | P0 | 1j | 🔴 |
| Intégrer avec `AgentOrchestrator` | P0 | 0.5j | 🔴 |
| Export conversations (JSON/Markdown) | P2 | 0.5j | 🔴 |

#### 2.4 Secure Key Storage (2 jours)

| Tâche | Priorité | Effort | Statut |
|-------|----------|--------|--------|
| Créer `ragkit/security/keyring.py` | P0 | 0.5j | 🔴 |
| Intégrer avec `keyring` system | P0 | 0.5j | 🔴 |
| Fallback chiffrement local | P1 | 0.5j | 🔴 |
| Tests multi-plateforme | P0 | 0.5j | 🔴 |

**Critères de succès Phase 2 :**
- [ ] SQLite remplace stockage fichier
- [ ] Multiple knowledge bases supportées
- [ ] Conversations persistées entre sessions
- [ ] Clés API stockées de façon sécurisée

---

## 🖥️ Phase 3 : Tauri Shell (Base)

**Durée** : 2 semaines  
**Objectif** : Créer le shell desktop avec communication Python

### Tâches détaillées

#### 3.1 Setup Projet Tauri (3 jours)

| Tâche | Priorité | Effort | Statut |
|-------|----------|--------|--------|
| Initialiser projet Tauri + Vite + React | P0 | 0.5j | 🔴 |
| Configurer sidecar Python | P0 | 1j | 🔴 |
| Setup build cross-platform | P0 | 1j | 🔴 |
| CI/CD GitHub Actions | P0 | 0.5j | 🔴 |

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

#### 3.2 Communication IPC (4 jours)

| Tâche | Priorité | Effort | Statut |
|-------|----------|--------|--------|
| Définir protocole IPC (JSON-RPC?) | P0 | 0.5j | 🔴 |
| Implémenter côté Rust (Tauri commands) | P0 | 1j | 🔴 |
| Implémenter côté Python (serveur) | P0 | 1j | 🔴 |
| Gestion lifecycle (start/stop backend) | P0 | 1j | 🔴 |
| Error handling et reconnection | P0 | 0.5j | 🔴 |

```typescript
// Exemple commande Tauri
import { invoke } from '@tauri-apps/api/tauri';

async function query(kbId: string, question: string): Promise<QueryResult> {
  return await invoke('query', { kbId, question });
}
```

#### 3.3 Backend Startup (3 jours)

| Tâche | Priorité | Effort | Statut |
|-------|----------|--------|--------|
| Script démarrage Python sidecar | P0 | 1j | 🔴 |
| Health check et auto-restart | P0 | 0.5j | 🔴 |
| Logging centralisé | P0 | 0.5j | 🔴 |
| Shutdown graceful | P0 | 0.5j | 🔴 |
| Port allocation dynamique | P1 | 0.5j | 🔴 |

**Critères de succès Phase 3 :**
- [ ] App Tauri démarre sur macOS/Windows/Linux
- [ ] Backend Python démarre automatiquement
- [ ] Communication bidirectionnelle fonctionne
- [ ] Build CI produit des artifacts

---

## 🎨 Phase 4 : UI Core

**Durée** : 2 semaines  
**Objectif** : Interfaces utilisateur principales

### Tâches détaillées

#### 4.1 Design System (2 jours)

| Tâche | Priorité | Effort | Statut |
|-------|----------|--------|--------|
| Choisir UI library (shadcn/ui?) | P0 | 0.5j | 🔴 |
| Définir palette couleurs / thème | P0 | 0.5j | 🔴 |
| Composants de base (Button, Input, etc.) | P0 | 1j | 🔴 |

#### 4.2 Écran Configuration (3 jours)

| Tâche | Priorité | Effort | Statut |
|-------|----------|--------|--------|
| Layout settings page | P0 | 0.5j | 🔴 |
| Section Embedding provider | P0 | 1j | 🔴 |
| Section LLM provider | P0 | 1j | 🔴 |
| Gestion clés API | P0 | 0.5j | 🔴 |

```
┌─────────────────────────────────────────┐
│  ⚙️ Settings                            │
├─────────────────────────────────────────┤
│                                         │
│  [General] [Providers] [Advanced]       │
│  ─────────────────────────────────────  │
│                                         │
│  Embedding Provider                     │
│  ┌─────────────────────────────────┐   │
│  │ ● Local (ONNX)                  │   │
│  │   Model: all-MiniLM-L6-v2       │   │
│  │   Status: ✓ Ready               │   │
│  └─────────────────────────────────┘   │
│                                         │
│  LLM Provider                           │
│  ┌─────────────────────────────────┐   │
│  │ ● Ollama                        │   │
│  │   Model: llama3.2:3b            │   │
│  │   Status: ✓ Connected           │   │
│  └─────────────────────────────────┘   │
│                                         │
│              [Save Changes]             │
└─────────────────────────────────────────┘
```

#### 4.3 Interface Chat (4 jours)

| Tâche | Priorité | Effort | Statut |
|-------|----------|--------|--------|
| Layout chat (messages list) | P0 | 1j | 🔴 |
| Input avec envoi | P0 | 0.5j | 🔴 |
| Affichage streaming | P0 | 1j | 🔴 |
| Citations sources (expandable) | P0 | 1j | 🔴 |
| Historique conversations | P1 | 0.5j | 🔴 |

#### 4.4 Gestion Knowledge Bases (3 jours)

| Tâche | Priorité | Effort | Statut |
|-------|----------|--------|--------|
| Liste des KB avec stats | P0 | 1j | 🔴 |
| Création nouvelle KB | P0 | 1j | 🔴 |
| Configuration sources (file picker) | P0 | 0.5j | 🔴 |
| Suppression avec confirmation | P0 | 0.5j | 🔴 |

**Critères de succès Phase 4 :**
- [ ] Utilisateur peut configurer providers
- [ ] Chat fonctionnel avec streaming
- [ ] Création/gestion KB via UI

---

## 🦙 Phase 5 : Ollama Integration

**Durée** : 2 semaines  
**Objectif** : Intégration complète avec Ollama

### Tâches détaillées

#### 5.1 Ollama Manager (3 jours)

| Tâche | Priorité | Effort | Statut |
|-------|----------|--------|--------|
| Créer `ragkit/llm/providers/ollama_manager.py` | P0 | 1j | 🔴 |
| Détection installation Ollama | P0 | 0.5j | 🔴 |
| Liste modèles installés | P0 | 0.5j | 🔴 |
| Pull model avec progress | P0 | 1j | 🔴 |

#### 5.2 UI Ollama (3 jours)

| Tâche | Priorité | Effort | Statut |
|-------|----------|--------|--------|
| Status indicator Ollama | P0 | 0.5j | 🔴 |
| Liste modèles avec download | P0 | 1j | 🔴 |
| Progress bar téléchargement | P0 | 0.5j | 🔴 |
| Instructions installation si absent | P0 | 0.5j | 🔴 |
| Link vers Ollama website | P0 | 0.5j | 🔴 |

#### 5.3 Fallback & Error Handling (2 jours)

| Tâche | Priorité | Effort | Statut |
|-------|----------|--------|--------|
| Retry logic sur timeout | P0 | 0.5j | 🔴 |
| Message si Ollama down | P0 | 0.5j | 🔴 |
| Suggestion utiliser API externe | P1 | 0.5j | 🔴 |
| Logs détaillés pour debug | P0 | 0.5j | 🔴 |

#### 5.4 Testing Multi-modèles (2 jours)

| Tâche | Priorité | Effort | Statut |
|-------|----------|--------|--------|
| Test llama3.2:3b | P0 | 0.5j | 🔴 |
| Test mistral:7b | P0 | 0.5j | 🔴 |
| Test phi3:mini | P0 | 0.5j | 🔴 |
| Documentation performances | P1 | 0.5j | 🔴 |

**Critères de succès Phase 5 :**
- [ ] UI affiche status Ollama
- [ ] Téléchargement modèles depuis UI
- [ ] Fallback graceful si Ollama absent

---

## ✨ Phase 6 : Polish & Alpha

**Durée** : 2 semaines  
**Objectif** : Expérience utilisateur fluide pour alpha

### Tâches détaillées

#### 6.1 Onboarding Wizard (3 jours)

| Tâche | Priorité | Effort | Statut |
|-------|----------|--------|--------|
| Écran bienvenue | P0 | 0.5j | 🔴 |
| Choix provider (local vs API) | P0 | 0.5j | 🔴 |
| Download modèle si local | P0 | 0.5j | 🔴 |
| Input clés API si externe | P0 | 0.5j | 🔴 |
| Création première KB | P0 | 0.5j | 🔴 |
| Tutorial overlay | P1 | 0.5j | 🔴 |

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│              🚀 Welcome to RAGKIT                           │
│                                                             │
│   Turn your documents into an intelligent                   │
│   knowledge base you can chat with.                         │
│                                                             │
│   ─────────────────────────────────────────────────────────│
│                                                             │
│   How would you like to run RAGKIT?                         │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐  │
│   │  🖥️  100% Local (Recommended)                       │  │
│   │      • Privacy: Your data never leaves your machine │  │
│   │      • Requires: ~500MB disk, Ollama                │  │
│   │      • Best for: Personal documents                 │  │
│   │                                              [Select]│  │
│   └─────────────────────────────────────────────────────┘  │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐  │
│   │  ☁️  Cloud APIs                                      │  │
│   │      • Uses: OpenAI, Anthropic, Cohere              │  │
│   │      • Requires: API keys                           │  │
│   │      • Best for: Better quality, faster             │  │
│   │                                              [Select]│  │
│   └─────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 6.2 Error Handling UX (3 jours)

| Tâche | Priorité | Effort | Statut |
|-------|----------|--------|--------|
| Toast notifications | P0 | 0.5j | 🔴 |
| Error boundaries React | P0 | 0.5j | 🔴 |
| Messages d'erreur user-friendly | P0 | 1j | 🔴 |
| Retry automatique avec feedback | P0 | 0.5j | 🔴 |
| Crash reporting (opt-in) | P2 | 0.5j | 🔴 |

#### 6.3 Performance Optimization (2 jours)

| Tâche | Priorité | Effort | Statut |
|-------|----------|--------|--------|
| Lazy loading composants | P0 | 0.5j | 🔴 |
| Memoization conversations | P0 | 0.5j | 🔴 |
| Startup time < 3s | P0 | 0.5j | 🔴 |
| Memory profiling | P1 | 0.5j | 🔴 |

#### 6.4 Alpha Release (2 jours)

| Tâche | Priorité | Effort | Statut |
|-------|----------|--------|--------|
| Build macOS signed | P0 | 0.5j | 🔴 |
| Build Windows signed | P0 | 0.5j | 🔴 |
| Build Linux (AppImage) | P0 | 0.5j | 🔴 |
| Distribution interne (10 testeurs) | P0 | 0.5j | 🔴 |

**Critères de succès Phase 6 :**
- [ ] First-run experience fluide
- [ ] Pas de crash bloquant
- [ ] 10 testeurs alpha actifs

---

## 🧪 Phase 7 : Beta Testing

**Durée** : 2 semaines  
**Objectif** : Valider avec 50+ utilisateurs réels

### Tâches

| Tâche | Priorité | Effort | Statut |
|-------|----------|--------|--------|
| Recrutement 50 beta testers | P0 | 1j | 🔴 |
| Setup feedback channel (Discord?) | P0 | 0.5j | 🔴 |
| Triage et fix bugs critiques | P0 | 5j | 🔴 |
| Amélioration basée sur feedback | P0 | 3j | 🔴 |
| Performance tuning final | P0 | 2j | 🔴 |

**Métriques beta :**
- Taux installation réussie : > 95%
- Taux complétion onboarding : > 80%
- Bugs critiques : 0
- NPS : > 30

---

## 🚀 Phase 8 : V1.5 Release

**Durée** : 2 semaines  
**Objectif** : Release publique

### Tâches

| Tâche | Priorité | Effort | Statut |
|-------|----------|--------|--------|
| Documentation utilisateur complète | P0 | 3j | 🔴 |
| Landing page website | P0 | 2j | 🔴 |
| Release notes | P0 | 0.5j | 🔴 |
| Distribution (GitHub releases) | P0 | 0.5j | 🔴 |
| Annonce (blog, social) | P0 | 1j | 🔴 |
| Support initial (FAQ, issues) | P0 | ongoing | 🔴 |

---

## 🌐 Phase 9 : Server Mode (V2.0)

**Durée** : 4-6 semaines  
**Objectif** : Version multi-utilisateurs

### Tâches haut niveau

| Feature | Effort | Priorité |
|---------|--------|----------|
| Multi-tenancy (Organizations) | 5j | P0 |
| Auth local (email/password) | 3j | P0 |
| Auth OIDC (SSO) | 3j | P1 |
| PostgreSQL migration | 3j | P0 |
| Qdrant cloud support | 2j | P0 |
| Redis pour sessions | 2j | P0 |
| Admin console basique | 5j | P1 |
| Deployment guide (Docker) | 2j | P0 |

---

## 🏢 Phase 10 : Enterprise (V2.5)

**Durée** : 4-6 semaines  
**Objectif** : Features entreprise

### Tâches haut niveau

| Feature | Effort | Priorité |
|---------|--------|----------|
| LDAP/SAML SSO | 5j | P0 |
| Audit logs | 3j | P0 |
| Role-based permissions | 3j | P0 |
| API rate limiting | 2j | P1 |
| Usage analytics | 3j | P1 |
| White-labeling | 3j | P2 |
| SLA et support | ongoing | P0 |

---

## 📊 Tableau de Bord

### Progression Globale

```
Phase 1 [██████████] 100%  ← À faire en premier
Phase 2 [░░░░░░░░░░]   0%
Phase 3 [░░░░░░░░░░]   0%
Phase 4 [░░░░░░░░░░]   0%
Phase 5 [░░░░░░░░░░]   0%
Phase 6 [░░░░░░░░░░]   0%
Phase 7 [░░░░░░░░░░]   0%
Phase 8 [░░░░░░░░░░]   0%
─────────────────────────
V1.5    [░░░░░░░░░░]   0%  Target: Mai 2026
```

### Risques Identifiés

| Risque | Impact | Probabilité | Mitigation |
|--------|--------|-------------|------------|
| Performance ONNX sur CPU | Medium | Medium | Benchmark early, fallback API |
| Complexité cross-platform | High | Medium | CI/CD dès Phase 3 |
| Ollama adoption | Low | Low | Support API externe |
| Tauri learning curve | Medium | Medium | Équipe frontend dédiée |

### Dépendances Critiques

```
Phase 1 ──▶ Phase 2 ──▶ Phase 4
                  │
Phase 3 ─────────┴────▶ Phase 4 ──▶ Phase 5 ──▶ Phase 6
```

---

## 📝 Notes de Mise à Jour

```
[05/02/2026] - Initial roadmap draft
- Defined 10 phases over 6 months
- Focus on V1.5 Desktop first
- Server mode planned for V2.0

[DATE] - [NOTE]
```

---

## 🔗 Documents Liés

- [RAGKIT_DESKTOP_SPECS.md](./RAGKIT_DESKTOP_SPECS.md) - Spécifications techniques détaillées
- [CONTEXT.md](./CONTEXT.md) - Contexte projet original
- [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) - Plan V1.0 (complété)
