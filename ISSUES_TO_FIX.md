# Issues Critiques à Corriger - RAGKIT Desktop v2.0.0

## 📋 Résumé des Problèmes Identifiés

Suite aux tests de la release v2.0.0, plusieurs problèmes critiques ont été identifiés qui empêchent l'utilisation normale de l'application. Ce document détaille chaque problème et indique où et comment le corriger.

---

## 🔴 Problème 1 : Application Entièrement en Anglais

### Description
L'interface est entièrement en anglais alors que l'application devrait supporter le français.

### Impact
- **Priorité** : Moyenne
- **Utilisateurs affectés** : Tous les utilisateurs francophones
- **Blocant** : Non, mais dégradation UX significative

### Localisation du Problème
- **Fichiers concernés** :
  - `desktop/src/pages/Onboarding.tsx`
  - `desktop/src/pages/Wizard/WelcomeStep.tsx`
  - `desktop/src/pages/Wizard/ProfileStep.tsx`
  - `desktop/src/pages/Wizard/FolderStep.tsx`
  - `desktop/src/pages/Wizard/ModelsStep.tsx`
  - `desktop/src/pages/Wizard/SummaryStep.tsx`
  - `desktop/src/pages/KnowledgeBases.tsx`
  - `desktop/src/pages/Settings.tsx`
  - `ragkit-ui/src/` (tous les composants)

### Comment Corriger

#### Option 1 : i18n avec react-i18next (Recommandé)

**Étape 1** : Installer les dépendances
```bash
cd desktop
npm install react-i18next i18next
```

**Étape 2** : Créer la structure de traduction
```
desktop/src/locales/
├── en.json
└── fr.json
```

**Étape 3** : Créer `desktop/src/i18n.ts`
```typescript
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import en from './locales/en.json';
import fr from './locales/fr.json';

i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      fr: { translation: fr }
    },
    lng: 'fr', // Langue par défaut
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false
    }
  });

export default i18n;
```

**Étape 4** : Créer les fichiers de traduction

`desktop/src/locales/fr.json` :
```json
{
  "wizard": {
    "welcome": {
      "title": "Bienvenue sur RAGKIT",
      "subtitle": "Créez votre système RAG en quelques minutes",
      "getStarted": "Commencer"
    },
    "folder": {
      "title": "Sélectionnez votre base de connaissances",
      "subtitle": "Choisissez le dossier contenant vos documents",
      "browse": "Parcourir",
      "placeholder": "Chemin vers votre dossier",
      "error": {
        "required": "Veuillez sélectionner un dossier",
        "notExists": "Ce dossier n'existe pas",
        "empty": "Ce dossier est vide"
      }
    },
    "profile": {
      "title": "Sélectionnez votre profil",
      "beginner": "Débutant",
      "intermediate": "Intermédiaire",
      "expert": "Expert"
    }
  },
  "settings": {
    "title": "Paramètres",
    "general": "Général",
    "advanced": "Avancé",
    "save": "Enregistrer"
  },
  "knowledgeBases": {
    "title": "Bases de Connaissances",
    "empty": "Aucune base de connaissances",
    "create": "Créer",
    "addDocuments": "Ajouter des documents",
    "addFolder": "Ajouter un dossier"
  }
}
```

**Étape 5** : Utiliser dans les composants
```typescript
import { useTranslation } from 'react-i18next';

function WelcomeStep() {
  const { t } = useTranslation();

  return (
    <div>
      <h1>{t('wizard.welcome.title')}</h1>
      <p>{t('wizard.welcome.subtitle')}</p>
      <button>{t('wizard.welcome.getStarted')}</button>
    </div>
  );
}
```

**Étape 6** : Ajouter un sélecteur de langue
```typescript
import { useTranslation } from 'react-i18next';

function LanguageSelector() {
  const { i18n } = useTranslation();

  return (
    <select value={i18n.language} onChange={(e) => i18n.changeLanguage(e.target.value)}>
      <option value="fr">Français</option>
      <option value="en">English</option>
    </select>
  );
}
```

---

## 🔴 Problème 2 : Bouton "Browse" Ne Fonctionne Pas

### Description
Le bouton "Browse" pour sélectionner un dossier ne permet pas de sélectionner un dossier. Il n'ouvre pas de dialogue de sélection.

### Impact
- **Priorité** : CRITIQUE
- **Utilisateurs affectés** : Tous
- **Blocant** : OUI - empêche la création de base de connaissances

### Localisation du Problème
**Fichier** : `desktop/src/pages/Wizard/FolderStep.tsx` (lignes 30-50 environ)

### Code Actuel Problématique
```typescript
<button onClick={() => {
  // Code manquant ou incorrect
  console.log('Browse clicked');
}}>
  Browse
</button>
```

### Comment Corriger

#### Solution : Utiliser l'API Tauri pour ouvrir un dialogue

**Fichier à modifier** : `desktop/src/pages/Wizard/FolderStep.tsx`

**Code à remplacer** :
```typescript
import { useState } from 'react';
import { open } from '@tauri-apps/api/dialog';

function FolderStep() {
  const [folderPath, setFolderPath] = useState('');

  const handleBrowse = async () => {
    try {
      const selected = await open({
        directory: true,
        multiple: false,
        title: 'Sélectionnez votre dossier de base de connaissances'
      });

      if (selected && typeof selected === 'string') {
        setFolderPath(selected);
      }
    } catch (error) {
      console.error('Error selecting folder:', error);
    }
  };

  return (
    <div>
      <input
        type="text"
        value={folderPath}
        onChange={(e) => setFolderPath(e.target.value)}
        placeholder="Chemin vers votre dossier"
      />
      <button onClick={handleBrowse}>
        Parcourir
      </button>
    </div>
  );
}
```

**Dépendances à vérifier** :
```json
// desktop/package.json
{
  "dependencies": {
    "@tauri-apps/api": "^1.5.0"
  }
}
```

---

## 🔴 Problème 3 : Pas de Validation du Dossier Sélectionné

### Description
On peut continuer sans avoir sélectionné un dossier, ou avec un chemin invalide/inexistant.

### Impact
- **Priorité** : CRITIQUE
- **Utilisateurs affectés** : Tous
- **Blocant** : OUI - crée des bases de connaissances invalides

### Localisation du Problème
**Fichiers concernés** :
1. `desktop/src/pages/Wizard/FolderStep.tsx` - Validation côté frontend
2. `ragkit/desktop/wizard_api.py` - Validation côté backend

### Comment Corriger

#### Partie 1 : Validation Frontend

**Fichier** : `desktop/src/pages/Wizard/FolderStep.tsx`

```typescript
import { useState } from 'react';
import { exists, readDir } from '@tauri-apps/api/fs';
import { open } from '@tauri-apps/api/dialog';

function FolderStep({ onNext }: { onNext: (path: string) => void }) {
  const [folderPath, setFolderPath] = useState('');
  const [error, setError] = useState('');
  const [isValidating, setIsValidating] = useState(false);

  const validateFolder = async (path: string): Promise<boolean> => {
    setError('');

    if (!path || path.trim() === '') {
      setError('Veuillez sélectionner un dossier');
      return false;
    }

    setIsValidating(true);

    try {
      // Vérifier que le chemin existe
      const pathExists = await exists(path);
      if (!pathExists) {
        setError('Ce dossier n\'existe pas. Veuillez vérifier le chemin.');
        return false;
      }

      // Vérifier que c'est bien un dossier et qu'il contient des fichiers
      const entries = await readDir(path);
      if (entries.length === 0) {
        setError('Ce dossier est vide. Veuillez sélectionner un dossier contenant des documents.');
        return false;
      }

      // Vérifier qu'il y a au moins un fichier supporté
      const supportedExtensions = ['.pdf', '.txt', '.md', '.docx', '.html'];
      const hasValidFiles = entries.some(entry =>
        entry.name && supportedExtensions.some(ext => entry.name!.toLowerCase().endsWith(ext))
      );

      if (!hasValidFiles) {
        setError('Aucun document supporté trouvé (.pdf, .txt, .md, .docx, .html)');
        return false;
      }

      return true;
    } catch (err) {
      setError('Erreur lors de la validation du dossier');
      console.error('Validation error:', err);
      return false;
    } finally {
      setIsValidating(false);
    }
  };

  const handleNext = async () => {
    const isValid = await validateFolder(folderPath);
    if (isValid) {
      onNext(folderPath);
    }
  };

  const handleBrowse = async () => {
    const selected = await open({
      directory: true,
      multiple: false,
      title: 'Sélectionnez votre dossier de base de connaissances'
    });

    if (selected && typeof selected === 'string') {
      setFolderPath(selected);
      // Valider automatiquement après sélection
      await validateFolder(selected);
    }
  };

  return (
    <div>
      <h2>Sélectionnez votre base de connaissances</h2>
      <div>
        <input
          type="text"
          value={folderPath}
          onChange={(e) => setFolderPath(e.target.value)}
          placeholder="Chemin vers votre dossier"
        />
        <button onClick={handleBrowse}>
          Parcourir
        </button>
      </div>

      {error && (
        <div className="error-message" style={{ color: 'red', marginTop: '10px' }}>
          {error}
        </div>
      )}

      <button
        onClick={handleNext}
        disabled={!folderPath || isValidating || !!error}
      >
        {isValidating ? 'Validation...' : 'Suivant'}
      </button>
    </div>
  );
}
```

#### Partie 2 : Validation Backend

**Fichier** : `ragkit/desktop/wizard_api.py`

Ajouter une fonction de validation :
```python
import os
from pathlib import Path

def validate_knowledge_base_folder(folder_path: str) -> dict:
    """Validate that the folder is suitable for a knowledge base.

    Returns:
        dict: {"valid": bool, "error": str | None, "stats": dict}
    """
    if not folder_path:
        return {"valid": False, "error": "Folder path is required", "stats": {}}

    path = Path(folder_path)

    # Check if path exists
    if not path.exists():
        return {"valid": False, "error": f"Path does not exist: {folder_path}", "stats": {}}

    # Check if it's a directory
    if not path.is_dir():
        return {"valid": False, "error": "Path is not a directory", "stats": {}}

    # Check if we have read permissions
    if not os.access(path, os.R_OK):
        return {"valid": False, "error": "No read permission for this folder", "stats": {}}

    # Count supported files
    supported_extensions = {'.pdf', '.txt', '.md', '.docx', '.html', '.csv', '.json'}
    files = []
    total_size = 0

    try:
        for file_path in path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                files.append(file_path)
                total_size += file_path.stat().st_size
    except Exception as e:
        return {"valid": False, "error": f"Error scanning folder: {str(e)}", "stats": {}}

    if not files:
        return {
            "valid": False,
            "error": "No supported documents found in folder",
            "stats": {"files": 0, "size_mb": 0}
        }

    return {
        "valid": True,
        "error": None,
        "stats": {
            "files": len(files),
            "size_mb": round(total_size / (1024 * 1024), 2),
            "extensions": list(set(f.suffix for f in files))
        }
    }
```

Ajouter un endpoint dans le wizard :
```python
@router.post("/wizard/validate-folder")
async def validate_folder(request: dict) -> dict:
    """Validate a folder for knowledge base creation."""
    folder_path = request.get("folder_path")
    result = validate_knowledge_base_folder(folder_path)
    return result
```

---

## 🔴 Problème 4 : Aucune Base de Connaissances Créée

### Description
Après avoir renseigné un répertoire valide et terminé le wizard, aucune base de connaissances n'apparaît dans Knowledge Bases.

### Impact
- **Priorité** : CRITIQUE
- **Utilisateurs affectés** : Tous
- **Blocant** : OUI - l'application ne fonctionne pas

### Localisation du Problème
**Fichiers concernés** :
1. `desktop/src/pages/Wizard/SummaryStep.tsx` - Soumission finale
2. `ragkit/desktop/wizard_api.py` - Création de la KB
3. `ragkit/desktop/state.py` - Persistence de l'état

### Analyse
Le wizard ne persiste probablement pas la configuration et ne déclenche pas l'ingestion.

### Comment Corriger

#### Étape 1 : Compléter le SummaryStep

**Fichier** : `desktop/src/pages/Wizard/SummaryStep.tsx`

```typescript
import { useState } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { useNavigate } from 'react-router-dom';

function SummaryStep({ wizardData }: { wizardData: WizardData }) {
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleLaunch = async () => {
    setIsCreating(true);
    setError('');

    try {
      // Appeler l'API backend pour créer la KB
      const result = await invoke('create_knowledge_base', {
        config: {
          name: wizardData.kbName || 'Ma Base de Connaissances',
          folder_path: wizardData.folderPath,
          profile: wizardData.profile,
          embedding_model: wizardData.embeddingModel,
          llm_model: wizardData.llmModel,
        }
      });

      console.log('Knowledge base created:', result);

      // Déclencher l'ingestion
      await invoke('start_ingestion', {
        kb_id: result.kb_id
      });

      // Rediriger vers Knowledge Bases
      navigate('/knowledge-bases');
    } catch (err) {
      console.error('Error creating KB:', err);
      setError('Erreur lors de la création de la base de connaissances');
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div>
      <h2>Résumé de votre configuration</h2>

      <div className="summary">
        <p><strong>Dossier :</strong> {wizardData.folderPath}</p>
        <p><strong>Profil :</strong> {wizardData.profile}</p>
        <p><strong>Modèle d'embedding :</strong> {wizardData.embeddingModel}</p>
        <p><strong>Modèle LLM :</strong> {wizardData.llmModel}</p>
      </div>

      {error && <div className="error">{error}</div>}

      <button
        onClick={handleLaunch}
        disabled={isCreating}
      >
        {isCreating ? 'Création en cours...' : 'Lancer le RAG'}
      </button>
    </div>
  );
}
```

#### Étape 2 : Implémenter les Commandes Tauri

**Fichier** : `desktop/src-tauri/src/commands.rs`

Ajouter les commandes manquantes :
```rust
#[tauri::command]
async fn create_knowledge_base(config: serde_json::Value) -> Result<serde_json::Value, String> {
    // Appeler l'API Python backend
    let client = reqwest::Client::new();
    let response = client
        .post("http://localhost:8000/wizard/create")
        .json(&config)
        .send()
        .await
        .map_err(|e| e.to_string())?;

    let result = response.json()
        .await
        .map_err(|e| e.to_string())?;

    Ok(result)
}

#[tauri::command]
async fn start_ingestion(kb_id: String) -> Result<serde_json::Value, String> {
    let client = reqwest::Client::new();
    let response = client
        .post(&format!("http://localhost:8000/ingest/{}", kb_id))
        .send()
        .await
        .map_err(|e| e.to_string())?;

    let result = response.json()
        .await
        .map_err(|e| e.to_string())?;

    Ok(result)
}
```

Enregistrer dans `main.rs` :
```rust
fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            create_knowledge_base,
            start_ingestion,
            // ... autres commandes
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

#### Étape 3 : Implémenter l'API Backend

**Fichier** : `ragkit/desktop/wizard_api.py`

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import uuid

router = APIRouter()

class KnowledgeBaseConfig(BaseModel):
    name: str
    folder_path: str
    profile: str
    embedding_model: str
    llm_model: str

@router.post("/wizard/create")
async def create_knowledge_base(config: KnowledgeBaseConfig):
    """Create a new knowledge base from wizard config."""
    try:
        # Générer un ID unique
        kb_id = str(uuid.uuid4())

        # Sauvegarder la configuration
        kb_config = {
            "id": kb_id,
            "name": config.name,
            "folder_path": config.folder_path,
            "profile": config.profile,
            "embedding_model": config.embedding_model,
            "llm_model": config.llm_model,
            "created_at": datetime.now().isoformat(),
            "status": "created"
        }

        # Sauvegarder dans state
        from ragkit.desktop.state import save_knowledge_base
        save_knowledge_base(kb_config)

        return {"kb_id": kb_id, "status": "created"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ingest/{kb_id}")
async def start_ingestion(kb_id: str):
    """Start document ingestion for a knowledge base."""
    try:
        from ragkit.desktop.state import get_knowledge_base
        from ragkit.ingestion import IngestionPipeline

        kb_config = get_knowledge_base(kb_id)
        if not kb_config:
            raise HTTPException(status_code=404, detail="Knowledge base not found")

        # Démarrer l'ingestion en arrière-plan
        # TODO: Implémenter l'ingestion asynchrone

        return {"status": "ingestion_started", "kb_id": kb_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Fichier** : `ragkit/desktop/state.py`

```python
import json
from pathlib import Path
from typing import Optional

STATE_FILE = Path.home() / ".ragkit" / "knowledge_bases.json"

def save_knowledge_base(kb_config: dict):
    """Save knowledge base configuration."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Charger les KBs existantes
    kbs = []
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            kbs = json.load(f)

    # Ajouter la nouvelle KB
    kbs.append(kb_config)

    # Sauvegarder
    with open(STATE_FILE, 'w') as f:
        json.dump(kbs, f, indent=2)

def get_knowledge_bases() -> list[dict]:
    """Get all knowledge bases."""
    if not STATE_FILE.exists():
        return []

    with open(STATE_FILE, 'r') as f:
        return json.load(f)

def get_knowledge_base(kb_id: str) -> Optional[dict]:
    """Get a specific knowledge base by ID."""
    kbs = get_knowledge_bases()
    for kb in kbs:
        if kb.get('id') == kb_id:
            return kb
    return None
```

---

## 🔴 Problème 5 : Settings Ne Respectent Pas le Design Prévu

### Description
Les Settings ne montrent pas les niveaux Beginner/Intermediate/Expert comme prévu dans les documents de spécification.

### Impact
- **Priorité** : Moyenne
- **Utilisateurs affectés** : Tous
- **Blocant** : Non, mais manque de fonctionnalités

### Localisation du Problème
**Fichiers concernés** :
1. `desktop/src/pages/Settings.tsx` - Interface actuelle
2. Documents de référence :
   - `ragkit-parcours-utilisateur.md`
   - `parametres_rag_exhaustif.md`

### Design Attendu (selon les specs)

L'interface Settings devrait avoir :
1. **Sélecteur de niveau d'expertise** (Débutant/Intermédiaire/Expert)
2. **Onglets contextuels selon le niveau** :
   - Débutant : Général uniquement
   - Intermédiaire : Général + Avancé
   - Expert : Général + Avancé + JSON Editor

### Comment Corriger

#### Créer la nouvelle structure Settings

**Fichier** : `desktop/src/pages/Settings.tsx`

```typescript
import { useState } from 'react';
import { ExpertiseLevelSelector } from '../components/settings/ExpertiseLevelSelector';
import { GeneralSettings } from '../components/settings/GeneralSettings';
import { IntermediateSettings } from '../components/settings/IntermediateSettings';
import { ExpertJsonEditor } from '../components/settings/ExpertJsonEditor';

type ExpertiseLevel = 'beginner' | 'intermediate' | 'expert';

export default function Settings() {
  const [expertiseLevel, setExpertiseLevel] = useState<ExpertiseLevel>('beginner');
  const [activeTab, setActiveTab] = useState('general');

  const tabs = expertiseLevel === 'beginner'
    ? ['general']
    : expertiseLevel === 'intermediate'
    ? ['general', 'advanced']
    : ['general', 'advanced', 'json'];

  return (
    <div className="settings-page">
      <div className="settings-header">
        <h1>Paramètres</h1>
        <ExpertiseLevelSelector
          level={expertiseLevel}
          onChange={setExpertiseLevel}
        />
      </div>

      <div className="settings-tabs">
        {tabs.map(tab => (
          <button
            key={tab}
            className={activeTab === tab ? 'active' : ''}
            onClick={() => setActiveTab(tab)}
          >
            {tab === 'general' && 'Général'}
            {tab === 'advanced' && 'Avancé'}
            {tab === 'json' && 'JSON'}
          </button>
        ))}
      </div>

      <div className="settings-content">
        {activeTab === 'general' && <GeneralSettings />}
        {activeTab === 'advanced' && <IntermediateSettings />}
        {activeTab === 'json' && <ExpertJsonEditor />}
      </div>
    </div>
  );
}
```

#### Créer les composants Settings

**Fichier** : `desktop/src/components/settings/ExpertiseLevelSelector.tsx`

```typescript
type Props = {
  level: 'beginner' | 'intermediate' | 'expert';
  onChange: (level: 'beginner' | 'intermediate' | 'expert') => void;
};

export function ExpertiseLevelSelector({ level, onChange }: Props) {
  return (
    <div className="expertise-selector">
      <label>Niveau d'expertise</label>
      <select value={level} onChange={(e) => onChange(e.target.value as any)}>
        <option value="beginner">Débutant</option>
        <option value="intermediate">Intermédiaire</option>
        <option value="expert">Expert</option>
      </select>
    </div>
  );
}
```

**Fichier** : `desktop/src/components/settings/GeneralSettings.tsx`

```typescript
export function GeneralSettings() {
  return (
    <div className="general-settings">
      <h2>Paramètres Généraux</h2>

      <div className="setting-group">
        <h3>Modèle d'Embedding</h3>
        <select>
          <option>ONNX Local (Offline)</option>
          <option>OpenAI</option>
        </select>
      </div>

      <div className="setting-group">
        <h3>Chunking</h3>
        <label>Stratégie</label>
        <select>
          <option>Fixed</option>
          <option>Parent-Child</option>
          <option>Sliding Window</option>
        </select>

        <label>Taille des chunks</label>
        <input type="number" defaultValue={512} />

        <label>Overlap</label>
        <input type="number" defaultValue={50} />
      </div>

      <div className="setting-group">
        <h3>Retrieval</h3>
        <label>Architecture</label>
        <select>
          <option>Hybrid</option>
          <option>Semantic</option>
          <option>Lexical</option>
        </select>

        <label>Top K</label>
        <input type="number" defaultValue={10} />
      </div>
    </div>
  );
}
```

---

## 📊 Résumé des Fichiers à Modifier

### Priorité CRITIQUE (blocants)
1. ✅ `desktop/src/pages/Wizard/FolderStep.tsx` - Fix Browse + Validation
2. ✅ `desktop/src/pages/Wizard/SummaryStep.tsx` - Créer KB
3. ✅ `desktop/src-tauri/src/commands.rs` - Commandes Tauri
4. ✅ `ragkit/desktop/wizard_api.py` - API backend
5. ✅ `ragkit/desktop/state.py` - Persistence

### Priorité HAUTE (UX dégradée)
6. ✅ `desktop/src/i18n.ts` - Configuration i18n
7. ✅ `desktop/src/locales/fr.json` - Traductions françaises
8. ✅ `desktop/src/pages/Settings.tsx` - Nouvelle structure Settings

### Priorité MOYENNE (améliorations)
9. ✅ `desktop/src/components/settings/*` - Composants Settings
10. ✅ Tests E2E pour le workflow complet

---

## 🔧 Ordre de Correction Recommandé

1. **Jour 1 : Problèmes critiques**
   - Fixer le bouton Browse (P2)
   - Ajouter validation (P3)
   - Fixer la création de KB (P4)

2. **Jour 2 : i18n**
   - Setup i18n (P1)
   - Traduire tous les composants

3. **Jour 3 : Settings**
   - Refactorer Settings (P5)
   - Ajouter niveaux d'expertise

4. **Jour 4 : Tests**
   - Tester le workflow complet
   - Corriger bugs additionnels

---

## 🧪 Tests à Effectuer Après Corrections

### Test 1 : Wizard Complet
- [ ] Ouvrir l'application
- [ ] Cliquer "Commencer"
- [ ] Cliquer "Browse" → dialogue s'ouvre
- [ ] Sélectionner dossier invalide → erreur affichée
- [ ] Sélectionner dossier vide → erreur affichée
- [ ] Sélectionner dossier valide → validation OK
- [ ] Continuer jusqu'à Summary
- [ ] Cliquer "Lancer" → KB créée
- [ ] Redirection vers Knowledge Bases
- [ ] KB apparaît dans la liste

### Test 2 : i18n
- [ ] Changer langue en français → tout en français
- [ ] Changer langue en anglais → tout en anglais
- [ ] Redémarrer app → langue persiste

### Test 3 : Settings
- [ ] Niveau Débutant → 1 onglet (Général)
- [ ] Niveau Intermédiaire → 2 onglets (Général, Avancé)
- [ ] Niveau Expert → 3 onglets (Général, Avancé, JSON)
- [ ] Modifier paramètres → sauvegarde OK

---

## 📞 Contact Développeur

Si des clarifications sont nécessaires sur ces corrections :
- Documenter les questions dans un fichier `QUESTIONS.md`
- Créer des issues GitHub pour chaque problème
- Prioriser selon le tableau ci-dessus

---

**Date de création** : 10 février 2026
**Version RAGKIT** : v2.0.0
**Statut** : À corriger avant release v2.0.1
