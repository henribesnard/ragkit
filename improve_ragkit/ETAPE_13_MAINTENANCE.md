# Etape 13 : MISE A JOUR & MAINTENANCE

## Objectif
Implementer l'indexation incrementale, le versioning des documents/index, et les strategies de refresh.

---

## Phase 1 : Audit de l'Existant

### Ce qui existe
| Composant | Fichier | Etat |
|-----------|---------|------|
| MaintenanceConfigV2 | `ragkit/config/schema_v2.py` | incremental_indexing, update_strategy, versioning, refresh - NON branche |
| IngestionState | `ragkit/state/models.py` | last_run, last_stats, is_running, pending/total documents/chunks |
| UI | `Settings.tsx` | Aucun parametre maintenance |

### Ce qui manque
- Indexation incrementale (detecter les nouveaux/modifies/supprimes)
- Versioning des documents (garder l'historique)
- Versioning de l'index (rollback possible)
- Strategies de refresh (scheduled, on_demand)
- UI pour la maintenance

---

## Phase 2 : Indexation Incrementale

### 2.1 Creer `ragkit/maintenance/incremental.py`

```python
class IncrementalIndexer:
    """Gere l'indexation incrementale des documents."""

    def __init__(self, vector_store, document_registry):
        self.vector_store = vector_store
        self.registry = document_registry

    async def detect_changes(self, source_path: str) -> ChangeSet:
        """Detecte les documents nouveaux, modifies et supprimes."""
        current_files = self._scan_directory(source_path)
        known_files = self.registry.get_all()

        added = [f for f in current_files if f.path not in known_files]
        modified = [
            f for f in current_files
            if f.path in known_files and f.hash != known_files[f.path].hash
        ]
        removed = [
            f for f in known_files.values()
            if f.path not in {cf.path for cf in current_files}
        ]

        return ChangeSet(added=added, modified=modified, removed=removed)

    async def apply_changes(self, changes: ChangeSet) -> dict:
        """Applique les changements detectes."""
        stats = {"added": 0, "updated": 0, "removed": 0}

        # Supprimer les documents retires
        for doc in changes.removed:
            await self.vector_store.delete_by_document_id(doc.document_id)
            self.registry.remove(doc.path)
            stats["removed"] += 1

        # Mettre a jour les documents modifies (supprimer puis re-ingerer)
        for doc in changes.modified:
            await self.vector_store.delete_by_document_id(doc.document_id)
            # Re-ingerer le document modifie
            stats["updated"] += 1

        # Ajouter les nouveaux documents
        for doc in changes.added:
            # Ingerer le nouveau document
            stats["added"] += 1

        return stats
```

### 2.2 Document Registry

```python
class DocumentRegistry:
    """Registre des documents indexes avec leur hash et metadonnees."""

    def __init__(self, path: Path):
        self.path = path
        self._registry: dict[str, DocumentEntry] = {}

    def register(self, path: str, document_id: str, content_hash: str):
        """Enregistre un document indexe."""

    def get_all(self) -> dict[str, DocumentEntry]:
        """Retourne tous les documents enregistres."""

    def remove(self, path: str):
        """Supprime un document du registre."""

    def save(self):
        """Persiste le registre sur disque."""

    def load(self):
        """Charge le registre depuis le disque."""
```

---

## Phase 3 : Versioning

### 3.1 Document Versioning

```python
class DocumentVersionManager:
    """Gere les versions des documents."""

    def create_version(self, document_id: str, content: str, metadata: dict) -> str:
        """Cree une nouvelle version du document, retourne le version_id."""

    def get_version(self, document_id: str, version: str) -> dict | None:
        """Recupere une version specifique."""

    def list_versions(self, document_id: str) -> list[dict]:
        """Liste les versions d'un document."""

    def rollback(self, document_id: str, version: str):
        """Restaure une version precedente."""
```

### 3.2 Index Versioning

```python
class IndexVersionManager:
    """Gere les versions de l'index vectoriel."""

    def snapshot(self, name: str) -> str:
        """Cree un snapshot de l'index actuel."""

    def restore(self, snapshot_id: str):
        """Restaure un snapshot."""

    def list_snapshots(self) -> list[dict]:
        """Liste les snapshots disponibles."""
```

---

## Phase 4 : Strategies de Refresh

### 4.1 Creer `ragkit/maintenance/refresh.py`

```python
class RefreshManager:
    """Gere les strategies de rafraichissement de l'index."""

    def __init__(self, config: MaintenanceConfigV2, indexer: IncrementalIndexer):
        self.config = config
        self.indexer = indexer
        self._scheduler = None

    async def start_scheduled(self):
        """Demarre le refresh periodique."""
        if self.config.refresh_strategy == "scheduled" and self.config.auto_refresh_interval:
            # Lancer un task periodique
            while True:
                await self.refresh()
                await asyncio.sleep(self.config.auto_refresh_interval)

    async def refresh(self) -> dict:
        """Execute un cycle de refresh."""
        if self.config.update_strategy == "append":
            return await self._append_only()
        elif self.config.update_strategy == "upsert":
            return await self._upsert()
        elif self.config.update_strategy == "full_reindex":
            return await self._full_reindex()

    async def _append_only(self) -> dict:
        """N'ajoute que les nouveaux documents."""

    async def _upsert(self) -> dict:
        """Ajoute les nouveaux et met a jour les modifies."""

    async def _full_reindex(self) -> dict:
        """Reindexe tout depuis zero."""
```

---

## Phase 5 : UI - Exposition des Parametres

### Settings.tsx - Section "Maintenance"

Ajouter dans l'onglet "advanced" :
- **Incremental Indexing** : Checkbox enabled (defaut: false)
- **Update Strategy** : Select (append / upsert / full_reindex)
- **Document Versioning** : Checkbox enabled (defaut: false)
- **Auto Refresh** : Checkbox enabled + intervalle en secondes
- **Refresh Strategy** : Select (scheduled / on_demand)

### KnowledgeBases.tsx - Actions de maintenance

Ajouter des boutons dans la page des bases de connaissances :
- "Refresh" : Declenche un cycle de refresh on-demand
- "Reindex" : Declenche une reindexation complete
- "Snapshot" : Cree un snapshot de l'index

---

## Phase 6 : Tests & Validation

### Tests
```
tests/unit/test_maintenance.py
  - test_detect_new_files
  - test_detect_modified_files
  - test_detect_removed_files
  - test_apply_changes
  - test_document_registry
  - test_document_versioning

tests/integration/test_incremental.py
  - test_incremental_indexing_new_file
  - test_incremental_indexing_modified_file
  - test_incremental_indexing_removed_file
  - test_full_reindex
```

### Validation
1. Builder dans `.build/`
2. Ingester des documents
3. Ajouter un nouveau fichier dans le dossier source
4. Lancer un refresh -> verifier que seul le nouveau est indexe
5. Modifier un fichier -> verifier la mise a jour
6. Supprimer un fichier -> verifier la suppression de l'index

---

## Fichiers Impactes

| Action | Fichier |
|--------|---------|
| CREER | `ragkit/maintenance/__init__.py` |
| CREER | `ragkit/maintenance/incremental.py` |
| CREER | `ragkit/maintenance/registry.py` |
| CREER | `ragkit/maintenance/versioning.py` |
| CREER | `ragkit/maintenance/refresh.py` |
| MODIFIER | `desktop/src/pages/Settings.tsx` |
| MODIFIER | `desktop/src/pages/KnowledgeBases.tsx` |
| MODIFIER | `desktop/src/lib/ipc.ts` |
| MODIFIER | `desktop/src-tauri/src/commands.rs` |
| CREER | `tests/unit/test_maintenance.py` |
| CREER | `tests/integration/test_incremental.py` |

---

## Criteres de Validation

- [ ] Detection des changements (ajout/modification/suppression)
- [ ] Indexation incrementale fonctionnelle
- [ ] Document registry persiste
- [ ] Document versioning fonctionnel
- [ ] Strategies de refresh (append, upsert, full_reindex)
- [ ] Parametres exposes dans l'UI
- [ ] Actions de maintenance dans la page KB
- [ ] Tests passent
- [ ] Build et test manuel OK
