# ÉTAPE 1 : INGESTION & PRÉPROCESSING

## Objectif
Permettre à l'utilisateur de charger sa base de connaissances locale, d'analyser son contenu, de filtrer les documents pertinents et de valider les métadonnées avant l'indexation.

## Workflow Utilisateur

### 1. Sélection du Répertoire Source
- **Action Utilisateur** : L'utilisateur lance l'application (ou va dans "Ingestion").
- **Interface** : Demande de sélectionner le dossier racine de la base de connaissances.
- **Option** : "Inclure les sous-dossiers" (Checkbox : Oui/Non).

### 2. Analyse et Validation
- **Action Système** : Scanne le répertoire (et sous-répertoires si demandé).
- **Interface** : Affiche un rapport d'analyse :
    - Nombre total de fichiers détectés.
    - Répartition par type (ex: 15 PDF, 4 DOCX, 10 TXT).
    - Avertissements éventuels (fichiers corrompus, extensions non supportées).

### 3. Filtrage par Type
- **Interface** : Affiche des cases à cocher pour les types de documents détectés.
- **Logique** : Seuls les types *présents* dans le répertoire sont affichés.
- **Action Utilisateur** : Coche/décoche les extensions à inclure (ex: garder PDF et DOCX, ignorer TXT).

### 4. Extraction et Revue des Métadonnées
- **Action Système** : 
    - Extrait les métadonnées techniques automatiquement.
    - Pré-remplit les métadonnées fonctionnelles (Titre, Auteur, Date...).
- **Interface** : Tableau ou liste des documents sélectionnés.
- **Visibilité** :
    - **Affiché/Modifiable** : Métadonnées fonctionnelles (Titre, Auteur, Tags, Confidentialité...).
    - **Masqué (Système)** : Métadonnées techniques (Encoding, Hash, File path...).
- **Action Utilisateur** : Corrige ou valide les métadonnées proposées.

### 5. Configuration Finale de l'Ingestion
- **Interface** : Affiche les paramètres globaux de l'étape 1 (ex: Stratégie de chunking, OCR activé/désactivé).
- **Valeurs par défaut** : Pré-remplies par le système (basées sur des best practices ou l'analyse précédente).
- **Action Utilisateur** : Ajuste si besoin et lance l'ingestion finale.

---

## Modèle de Données (Metadata Schema)

### DocumentMetadata

#### Hiérarchie organisationnelle
| Champ | Description | Visibilité |
|---|---|---|
| `tenant` | Organisation / client | Système / Config |
| `domain` | Domaine métier | Utilisateur |
| `subdomain` | Sous-domaine | Utilisateur |

#### Identification document
| Champ | Description | Visibilité |
|---|---|---|
| `document_id` | ID unique généré | Système |
| `title` | Extrait du H1 ou nom de fichier | **Utilisateur (Modifiable)** |
| `author` | Extrait des métadonnées PDF/DOCX | **Utilisateur (Modifiable)** |
| `source` | Nom du fichier | Utilisateur (Lecture) |
| `source_path` | Chemin relatif | Système |
| `source_type` | pdf, docx, md, txt, html, csv | Utilisateur (Lecture) |
| `source_url` | URL d'origine si applicable | Utilisateur |
| `mime_type` | MIME type détecté | Système |

#### Temporalité
| Champ | Description | Visibilité |
|---|---|---|
| `created_at` | Date de création du document | Utilisateur |
| `modified_at` | Dernière modification | Utilisateur |
| `ingested_at` | Timestamp d'ingestion | Système |
| `version` | Version du document | Système / Utilisateur |

#### Contenu (auto-détecté)
| Champ | Description | Visibilité |
|---|---|---|
| `language` | Langue ISO 639-1 | Utilisateur (Modifiable) |
| `page_count` | Nombre de pages | Utilisateur |
| `word_count` | Nombre de mots | Système |
| `char_count` | Nombre de caractères | Système |
| `has_tables` | Booléen | Système |
| `has_images` | Booléen | Système |
| `has_code` | Booléen | Système |
| `encoding` | Encodage détecté | Système |

#### Classification
| Champ | Description | Visibilité |
|---|---|---|
| `tags` | Liste libre | **Utilisateur (Modifiable)** |
| `category` | Catégorie prédéfinie | **Utilisateur (Modifiable)** |
| `confidentiality` | public / internal / confidential / secret | **Utilisateur (Modifiable)** |
| `status` | draft / review / published / archived | **Utilisateur (Modifiable)** |

#### Parsing (système)
| Champ | Description | Visibilité |
|---|---|---|
| `parser_engine` | Moteur utilisé | Système |
| `ocr_applied` | OCR déclenché ou non | Système |
| `parsing_quality` | Score 0-1 | Système |
| `parsing_warnings` | Avertissements | Système |

#### Extensible
| Champ | Description | Visibilité |
|---|---|---|
| `custom` | Dictionnaire libre clé/valeur | Utilisateur |

### ChunkMetadata (Hérité + Enrichi)

**Hérité du document** : `document_id`, `tenant`, `domain`, `title`, `source`, `language`, `tags`

#### Spécifique au chunk
- `chunk_id`
- `chunk_index` (Position dans le document)
- `total_chunks`
- `chunk_strategy` (fixed / semantic / recursive)
- `chunk_size_tokens`
- `chunk_size_chars`

#### Contexte structurel
- `page_number`
- `section_title` (Titre de section parent)
- `heading_path` (Fil d'Ariane des headings)
- `paragraph_index`

#### Relations
- `previous_chunk_id`
- `next_chunk_id`
- `parent_chunk_id` (Pour le parent-child chunking)
