# Étape 1 : INGESTION & PREPROCESSING (Vertical Slice)

## 🎯 Objectif de l'Incrément
Permettre à l'utilisateur d'importer un document, de configurer finement comment il est lu (Parsing) et nettoyé (Preprocessing), et de **visualiser immédiatement le résultat**.

**Livrable** : Un `.exe` fonctionnel où l'utilisateur peut :
1.  Aller dans les "Settings > Ingestion".
2.  Modifier les paramètres (OCR, Lowercase, etc.).
3.  Uploader un fichier test ("Playground").
4.  Voir le texte extrait brut VS le texte nettoyé.

---

## 1. ⚙️ Paramètres à Exposer (Dashboard)

Ces paramètres proviennent de `parametres_rag_exhaustif.md` (sections 1.1 et 1.2).

### 1.1 Document Parsing
| Paramètre | Type UI | Description |
|-----------|---------|-------------|
| `ocr_enabled` | Toggle | Activer l'OCR pour les PDFs images |
| `ocr_language` | Dropdown | Langue (fra, eng, multi) |
| `table_extraction` | Dropdown | Stratégie (text, markdown, csv) |
| `header_detection` | Toggle | Détecter les titres (Markdown structure) |

### 1.2 Text Preprocessing
| Paramètre | Type UI | Description |
|-----------|---------|-------------|
| `lowercase` | Toggle | Tout mettre en minuscule |
| `remove_punctuation`| Toggle | Supprimer .,;:!? |
| `remove_urls` | Toggle | Supprimer http://... |
| `normalize_unicode` | Dropdown | NFC, NFD... |
| `deduplication` | Toggle | Ignorer les documents identiques |

---

## 2. 🖥️ Interface Utilisateur (Mockup)

### Page : `Settings > Ingestion`
Deux colonnes :
1.  **Configuration** (Gauche) : Liste des contrôles ci-dessus.
2.  **Live Preview** (Droite) :
    - Zone "Drop file to test"
    - Onglets résultats :
        - `Metadata` (JSON view)
        - `Raw Text` (Texte brut extrait)
        - `Cleaned Text` (Texte après preprocessing)

---

## 3. 🏗️ Architecture Backend (Python)

### 3.1 Modèles de Données (`ragkit/models.py`)
Mise à jour pour inclure les métadonnées riches.

```python
class DocumentMetadata(BaseModel):
    title: str
    page_count: int
    language: str
    # ... (voir schema complet plus bas)
```

### 3.2 Pipeline (`ragkit/ingestion/`)
- `parser_factory.py` : Sélectionne le bon parser (PDF, Docx...).
- `preprocessing.py` : Applique les filtres (Regex, Normalization) selon la config.
- `metadata_extractor.py` : Auto-détecte langue, auteur, titre.

### 3.3 API / Commandes Tauri (`desktop/src-tauri/src/commands.rs`)
Nouvelles commandes pour le frontend :
- `get_ingestion_config()`
- `save_ingestion_config(config)`
- `preview_ingestion(file_path, config)` -> Retourne `{raw, cleaned, metadata}`

---

## 4. 📝 Plan d'Implémentation

### Phase 4.1 : Backend Core (Jours 1-2)
- [ ] Créer `ragkit/ingestion/parsers/` (PDF, Docx, MD, Txt).
- [ ] Implémenter `ragkit/ingestion/preprocessing.py`.
- [ ] Implémenter `ragkit/ingestion/metadata.py`.
- [ ] Tests unitaires : `pytest tests/unit/test_ingestion.py`.

### Phase 4.2 : Backend API & Glue (Jour 3)
- [ ] Créer les schemas Pydantic pour la Config Ingestion.
- [ ] Exposer les commandes Tauri `preview_ingestion`.

### Phase 4.3 : Frontend UI (Jours 4-5)
- [ ] Créer `src/components/settings/IngestionSettings.tsx`.
- [ ] Créer `src/components/preview/IngestionPreview.tsx` (Split view).
- [ ] Intégrer dans la page Settings principale.

### Phase 4.4 : Validation & Build (Jour 6)
- [ ] Vérifier que changer "Lowercase" met bien à jour la preview en temps réel.
- [ ] Builder l'exe : `npm run tauri build`.
- [ ] Tester l'exe sur un Windows propre.

---

## 5. ✅ Critères de Validation (Definition of Done)

- [ ] L'application se lance (.exe).
- [ ] Je peux charger un PDF.
- [ ] Si j'active "Remove URLs", les liens disparaissent de la vue "Cleaned Text".
- [ ] Si j'active "OCR", un PDF scanné retourne du texte (au lieu de vide).
- [ ] Les métadonnées (nb pages, titre) sont correctes.
