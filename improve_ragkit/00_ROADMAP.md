# RAGKit v3 — Roadmap Incrémental & Vertical Slices

## 🎯 Philosophie : "Vertical Slices" & "Playable Builds"

Contrairement à une approche par couches (Backend puis Frontend), nous adoptons une stratégie de **"Vertical Slices"**.
À chaque étape, nous livrons une fonctionnalité complète, **du backend jusqu'à l'interface utilisateur (Dashboard)**.

### Règles d'Or pour chaque étape :
1.  **Exécutable** : À la fin de chaque étape, un `.exe` doit pouvoir être généré.
2.  **Configurable** : Les paramètres techniques développés (ex: OCR, Chunk size) doivent être exposés dans le **Dashboard Settings**.
3.  **Visualisable** : L'impact des réglages doit être visible immédiatement (ex: voir le texte brut après parsing, voir les chunks après découpage).
4.  **Testable** : L'utilisateur doit pouvoir valider "avec ses mains" sans ligne de commande.

---

## 🗺️ Vue d'Ensemble des Incréments

Chaque incrément s'appuie sur le précédent.

| # | Incrément | Fonctionnalité Utilisateur (.exe) | Backend | UI / Dashboard |
|---|-----------|-----------------------------------|---------|----------------|
| **1** | **Ingestion & Preprocessing** | Importer un fichier, voir son texte extrait et nettoyé selon réglages. | Pipelines Parsing (OCR, Tables) & Cleaning (Regex, Unicode) | Page "Ingestion Test" : Upload + Vue "Raw vs Clean" + Params |
| **2** | **Chunking & Structure** | Voir comment le document est découpé. | Chunkers (Fixed, Semantic, Recursive) | Page "Chunk Visualizer" : Liste des chunks, stats, search chunks |
| **3** | **Embedding & VectorStore** | Indexer et rechercher "texte vs texte" (similitude). | Embedders (Ollama/HF) + VectorDB (Chroma/Qdrant) | Page "Vector Explorer" : Search bar -> Top K matches (raw) |
| **4** | **Recherche Hybride** | Rechercher avec mots-clés + sémantique. | BM25 + Retrievers Hybrides + Fusion (RRF) | Settings "Retrieval" : Slider Alpha, Toggle Rerank, Results comparison |
| **5** | **LLM & RAG Loop** | Chatter avec ses documents. | LLM Client + Prompt Builder + Context Window | **Chat Interface** complet : Stream, Sources, Citations |
| **6** | **Reranking & Précision** | Améliorer la pertinence. | Cross-Encoders, Reranking Pipeline | Toggle Reranker, view scores "Before/After" rerank |
| **7** | **Performance & Cache** | Accélérer les réponses. | Caching (Query/Embedding), Async | Indicateurs de perf (latence) sur le dashboard |
| **8** | **Monitoring & Eval** | Evaluer la qualité. | Métriques (Faithfulness, Recall) | Page "Analytics" : Stats d'usage, Feedback loop |
| **9** | **Sécurité & Multi-user** | Gérer les accès. | Auth, RBA, Chiffrement | Login screen, Gestion utilisateurs |
| **10** | **Maintenance** | Mises à jour auto et indexation continue. | Watcher, Updater | Notifications de MAJ, Status watch |

---

## 📅 Plan d'Implémentation Détaillé

Les fichiers ci-dessous contiennent les spécifications techniques ET les maquettes fonctionnelles pour chaque incrément.

- [ETAPE_01_INGESTION_PREPROCESSING.md](./ETAPE_01_INGESTION_PREPROCESSING.md)
- [ETAPE_02_CHUNKING.md](./ETAPE_02_CHUNKING.md)
- [ETAPE_03_EMBEDDING.md](./ETAPE_03_EMBEDDING.md)
- [ETAPE_04_VECTORDB.md](./ETAPE_04_VECTORDB.md)
- [ETAPE_05_RECHERCHE_SEMANTIQUE.md](./ETAPE_05_RECHERCHE_SEMANTIQUE.md)
- [ETAPE_06_RECHERCHE_LEXICALE.md](./ETAPE_06_RECHERCHE_LEXICALE.md)
- [ETAPE_07_RECHERCHE_HYBRIDE.md](./ETAPE_07_RECHERCHE_HYBRIDE.md)
- [ETAPE_08_RERANKING.md](./ETAPE_08_RERANKING.md)
- [ETAPE_09_LLM_GENERATION.md](./ETAPE_09_LLM_GENERATION.md)
- [ETAPE_10_CACHE_PERFORMANCE.md](./ETAPE_10_CACHE_PERFORMANCE.md)
- [ETAPE_11_MONITORING_EVALUATION.md](./ETAPE_11_MONITORING_EVALUATION.md)
- [ETAPE_12_SECURITE_COMPLIANCE.md](./ETAPE_12_SECURITE_COMPLIANCE.md)
- [ETAPE_13_MAINTENANCE.md](./ETAPE_13_MAINTENANCE.md)

---

## 🛠 Méthodologie "Test-First"

Pour chaque ticket d'implémentation :
1.  **Définir l'interface** (Settings UI + Visualisation)
2.  **Implémenter le Backend** (Tests unitaires inclus)
3.  **Relier Backend <-> Frontend** (Commandes Tauri)
4.  **Builder l'EXE** et valider manuellement.
