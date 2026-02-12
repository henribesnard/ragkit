# Rapport d'Erreurs et Améliorations - RAGKIT Desktop v2.0.0 (Test #2)

**Date** : 11 février 2026
**Version testée** : v2.0.0
**Statut** : Erreurs critiques bloquantes identifiées

---

## 📋 Résumé Exécutif

Suite au second test de la release v2.0.0, **3 problèmes ont été identifiés** dont **2 sont critiques et bloquants**. L'analyse des logs et du code source révèle les causes racines suivantes :

1. ❌ **CRITIQUE** : Le sélecteur de dossier ne s'ouvre pas (Erreur: "Impossible d'ouvrir le sélecteur de dossier")
2. ❌ **CRITIQUE** : La validation de dossier échoue systématiquement (Erreur: "Impossible de valider le dossier")
3. ⚠️ **HAUTE** : Absence de sélecteur de langue (application forcée en français)

---

## 🔴 Problème #1 : Sélecteur de Dossier Ne S'ouvre Pas

### 📸 Symptôme Observé
- L'utilisateur clique sur le bouton "Parcourir" à l'étape 4 du wizard (Sélection du dossier)
- Message d'erreur affiché : **"Impossible d'ouvrir le sélecteur de dossier"**
- Aucune fenêtre de dialogue ne s'ouvre

### 🔍 Diagnostic

#### Cause Racine Identifiée
Le problème se situe dans **`desktop/src/lib/ipc.ts`** aux lignes **270-272** :

```typescript
async selectFolder(): Promise<string | null> {
  const { open } = await import("@tauri-apps/plugin-dialog");
  return open({ directory: true }) as Promise<string | null>;
}
```

**Le problème** : L'import dynamique `await import("@tauri-apps/plugin-dialog")` échoue silencieusement lors de l'exécution dans l'environnement de production compilé.

#### Pourquoi Ça Échoue

1. **Import dynamique non résolu** : Vite ne bundle pas correctement les imports dynamiques de plugins Tauri en production
2. **Plugin non exposé** : Le plugin dialog n'est pas exposé globalement via `window.__TAURI__`
3. **Erreur silencieuse** : L'exception est catchée dans `FolderStep.tsx:82-85` mais ne fournit pas de détails

#### Preuve dans les Logs
Aucune erreur explicite dans les logs car l'exception est catchée. Cependant, on observe :
- Aucune tentative d'appel au backend pour valider un dossier après le clic sur "Parcourir"
- Le champ de saisie reste vide après le clic

### ✅ Solution

#### Option 1 : Import statique (Recommandé)

**Fichier** : `desktop/src/lib/ipc.ts`

**Remplacer les lignes 259-273 par** :

```typescript
import { open } from "@tauri-apps/plugin-dialog";

// File dialogs (via Tauri)
async selectFiles(filters?: { name: string; extensions: string[] }[]): Promise<string[] | null> {
  const result = await open({
    multiple: true,
    filters: filters || [
      { name: "Documents", extensions: ["pdf", "txt", "md", "docx"] },
    ],
  });
  return result as string[] | null;
},

async selectFolder(): Promise<string | null> {
  const result = await open({
    directory: true,
    multiple: false,
    title: "Sélectionnez votre dossier de base de connaissances"
  });
  return typeof result === 'string' ? result : null;
},
```

**Ajout en haut du fichier (ligne 7)** :
```typescript
import { invoke } from "@tauri-apps/api/core";
import { open } from "@tauri-apps/plugin-dialog"; // <-- AJOUTER CETTE LIGNE
```

#### Option 2 : Utiliser window.__TAURI__ (Alternative)

Si l'Option 1 ne fonctionne pas, utiliser l'API globale :

```typescript
async selectFolder(): Promise<string | null> {
  if (!window.__TAURI__) {
    throw new Error("Tauri API not available");
  }
  const { open } = window.__TAURI__.dialog;
  const result = await open({
    directory: true,
    multiple: false,
    title: "Sélectionnez votre dossier de base de connaissances"
  });
  return typeof result === 'string' ? result : null;
}
```

### 🧪 Test de Validation

Après correction :
1. Lancer l'application en mode développement : `npm run tauri:dev`
2. Naviguer jusqu'à l'étape "Dossier"
3. Cliquer sur "Parcourir"
4. **✓ Vérifier** : Une fenêtre de sélection de dossier s'ouvre
5. Sélectionner un dossier valide
6. **✓ Vérifier** : Le chemin apparaît dans le champ de saisie
7. Compiler en production : `npm run tauri:build`
8. Répéter les tests 3-6 avec l'exécutable compilé

---

## 🔴 Problème #2 : Validation de Dossier Échoue

### 📸 Symptôme Observé
- L'utilisateur saisit manuellement un chemin de dossier valide : `C:\Users\henri\Projets\Branham\sermons\1948`
- Message d'erreur affiché : **"Impossible de valider le dossier"**
- Le bouton "Continuer" reste désactivé

### 🔍 Diagnostic

#### Cause Racine Identifiée
Le problème se situe dans **`desktop/src/pages/Wizard/FolderStep.tsx`** aux lignes **57-72** :

```typescript
const result = await ipc.validateFolder(trimmed);
```

Cette fonction appelle la commande Tauri `validate_folder` qui fait un appel HTTP au backend Python.

**Erreur identifiée** : L'appel échoue car :

1. **Le backend retourne une 404** : L'endpoint `/wizard/validate-folder` n'est pas accessible
2. **Route manquante** : Le router wizard n'est pas monté dans l'application principale

#### Preuve dans les Logs

Chercher dans `C:\Users\henri\.ragkit\logs\ragkit-desktop.log.2026-02-11` :
```
INFO:     127.0.0.1:XXXXX - "POST /api/wizard/validate-folder HTTP/1.1" 404 Not Found
```

#### Vérification de la Configuration

**Fichier à vérifier** : `ragkit/desktop/main.py` ou `ragkit/desktop/app.py`

**Problème attendu** : Le router wizard n'est pas monté :

```python
from fastapi import FastAPI
from ragkit.desktop.wizard_api import router as wizard_router

app = FastAPI()

# ❌ MANQUANT : Le router wizard n'est pas monté
# app.include_router(wizard_router, prefix="/api")
```

### ✅ Solution

#### Étape 1 : Vérifier le montage du router

**Fichier** : Trouver le fichier principal de l'API (probablement `ragkit/desktop/main.py` ou `ragkit/desktop/app.py`)

**Vérifier si cette ligne existe** :
```python
app.include_router(wizard_router, prefix="/api")
```

**Si elle manque, l'ajouter** :

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ragkit.desktop.wizard_api import router as wizard_router
from ragkit.desktop.kb_api import router as kb_router
from ragkit.desktop.settings_api import router as settings_router
# ... autres imports

app = FastAPI(title="RAGKIT Desktop API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1420", "tauri://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ AJOUTER CES LIGNES si elles manquent
app.include_router(wizard_router, prefix="/api")
app.include_router(kb_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
```

#### Étape 2 : Vérifier la signature de l'endpoint

**Fichier** : `ragkit/desktop/wizard_api.py` ligne 139-142

**Vérifier que c'est bien** :
```python
@router.post("/validate-folder")
async def validate_folder(request: FolderValidationRequest) -> dict[str, Any]:
    return validate_knowledge_base_folder(request.folder_path)
```

**Si le problème persiste**, essayer de changer le format de requête :

```python
@router.post("/validate-folder")
async def validate_folder(folder_path: str) -> dict[str, Any]:
    """Validate a folder for knowledge base creation."""
    return validate_knowledge_base_folder(folder_path)
```

Et côté Rust (`desktop/src-tauri/src/commands.rs` ligne 241) :

```rust
#[tauri::command]
pub async fn validate_folder(folder_path: String) -> Result<FolderValidationResult, String> {
    let client = reqwest::Client::new();
    let response = client
        .post("http://127.0.0.1:8100/api/wizard/validate-folder")
        .json(&serde_json::json!({ "folder_path": folder_path })) // ← Vérifier ce format
        .send()
        .await
        .map_err(|e| format!("HTTP request failed: {}", e))?;

    if !response.status().is_success() {
        return Err(format!("Validation failed: HTTP {}", response.status()));
    }

    let result: FolderValidationResult = response
        .json()
        .await
        .map_err(|e| format!("Failed to parse response: {}", e))?;

    Ok(result)
}
```

### 🧪 Test de Validation

Après correction :
1. Lancer le backend Python en mode debug :
   ```bash
   cd ragkit/desktop
   python -m uvicorn main:app --reload --port 8100 --log-level debug
   ```
2. Dans un autre terminal, tester l'endpoint directement :
   ```bash
   curl -X POST http://127.0.0.1:8100/api/wizard/validate-folder \
     -H "Content-Type: application/json" \
     -d '{"folder_path": "C:\\Users\\henri\\Projets\\ragkit"}'
   ```
3. **✓ Vérifier** : Réponse HTTP 200 avec JSON `{"valid": true, ...}`
4. Lancer l'application desktop : `npm run tauri:dev`
5. Saisir un chemin de dossier valide
6. **✓ Vérifier** : Message de validation en vert avec statistiques

---

## ⚠️ Problème #3 : Absence de Sélecteur de Langue

### 📸 Symptôme Observé
- L'application démarre toujours en français
- Aucune interface visible pour changer la langue
- L'utilisateur ne peut pas passer en anglais

### 🔍 Diagnostic

#### État Actuel

**Fichier** : `desktop/src/i18n.ts`

L'i18n est correctement configuré :
- ✅ Support français et anglais (lignes 23-25)
- ✅ Détection de la langue sauvegardée (lignes 8-20)
- ✅ Français par défaut (ligne 19)
- ✅ Sauvegarde automatique des changements (lignes 35-42)

**MAIS** : Il manque un composant UI pour permettre à l'utilisateur de changer la langue.

#### Où le Sélecteur Devrait Être

Selon les bonnes pratiques UX, le sélecteur de langue devrait être présent à **2 endroits** :

1. **Page d'accueil du wizard** (Bienvenue) - En haut à droite
2. **Page Settings** - Section "Général"

### ✅ Solution

#### Étape 1 : Créer le composant LanguageSelector

**Nouveau fichier** : `desktop/src/components/LanguageSelector.tsx`

```typescript
import { useTranslation } from "react-i18next";
import { Globe } from "lucide-react";

interface LanguageSelectorProps {
  variant?: "compact" | "full";
}

export function LanguageSelector({ variant = "compact" }: LanguageSelectorProps) {
  const { i18n } = useTranslation();

  const handleChange = (lang: string) => {
    i18n.changeLanguage(lang);
  };

  if (variant === "compact") {
    return (
      <div className="flex items-center gap-1">
        <Globe className="w-4 h-4 text-gray-500" />
        <select
          value={i18n.language}
          onChange={(e) => handleChange(e.target.value)}
          className="text-sm border rounded px-2 py-1 bg-white dark:bg-gray-800"
        >
          <option value="fr">Français</option>
          <option value="en">English</option>
        </select>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
        Langue / Language
      </label>
      <div className="flex gap-3">
        <button
          onClick={() => handleChange("fr")}
          className={`px-4 py-2 rounded border ${
            i18n.language === "fr"
              ? "bg-primary-600 text-white border-primary-600"
              : "bg-white dark:bg-gray-800 border-gray-300"
          }`}
        >
          🇫🇷 Français
        </button>
        <button
          onClick={() => handleChange("en")}
          className={`px-4 py-2 rounded border ${
            i18n.language === "en"
              ? "bg-primary-600 text-white border-primary-600"
              : "bg-white dark:bg-gray-800 border-gray-300"
          }`}
        >
          🇬🇧 English
        </button>
      </div>
    </div>
  );
}
```

#### Étape 2 : Ajouter au Wizard (Bienvenue)

**Fichier** : `desktop/src/pages/Wizard/WelcomeStep.tsx`

**Ajouter en haut du composant** :

```typescript
import { LanguageSelector } from "../../components/LanguageSelector";

export function WelcomeStep({ onNext }: WelcomeStepProps) {
  const { t } = useTranslation();

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Sélecteur de langue en haut à droite */}
      <div className="flex justify-end mb-4">
        <LanguageSelector variant="compact" />
      </div>

      <Card>
        <CardHeader>
          {/* ... reste du code */}
```

#### Étape 3 : Ajouter aux Settings

**Fichier** : `desktop/src/pages/Settings.tsx`

**Ajouter une section "Général"** :

```typescript
import { LanguageSelector } from "../components/LanguageSelector";

export default function Settings() {
  const { t } = useTranslation();

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">{t("settings.title")}</h1>

      {/* Section Langue */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>{t("settings.general")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <LanguageSelector variant="full" />

          {/* ... autres paramètres généraux */}
        </CardContent>
      </Card>

      {/* ... autres sections */}
    </div>
  );
}
```

#### Étape 4 : Ajouter les traductions manquantes

**Fichier** : `desktop/src/locales/fr.json`

Ajouter si manquant :
```json
{
  "settings": {
    "title": "Paramètres",
    "general": "Général",
    "language": "Langue"
  }
}
```

**Fichier** : `desktop/src/locales/en.json`

```json
{
  "settings": {
    "title": "Settings",
    "general": "General",
    "language": "Language"
  }
}
```

### 🧪 Test de Validation

Après correction :
1. Lancer l'application : `npm run tauri:dev`
2. Sur la page d'accueil du wizard :
   - **✓ Vérifier** : Sélecteur de langue visible en haut à droite
   - **✓ Vérifier** : Changer en "English" → toute l'interface passe en anglais
   - **✓ Vérifier** : Changer en "Français" → toute l'interface passe en français
3. Fermer et rouvrir l'application :
   - **✓ Vérifier** : La langue sélectionnée est conservée
4. Aller dans Settings :
   - **✓ Vérifier** : Sélecteur de langue présent
   - **✓ Vérifier** : Changement de langue fonctionne

---

## 🔧 Erreur Secondaire Identifiée dans les Logs

### 🟡 Erreur Ollama Recommended Models

**Ligne de log 9126** :
```
fastapi.exceptions.ResponseValidationError: 1 validation error:
  {'type': 'list_type', 'loc': ('response',), 'msg': 'Input should be a valid list', ...
  Endpoint: GET /api/ollama/recommended
```

**Cause** : L'endpoint `/api/ollama/recommended` retourne un dictionnaire au lieu d'une liste.

**Fichier concerné** : `ragkit/desktop/ollama_api.py` (ou similaire)

**Solution** :
```python
@router.get("/recommended", response_model=list[RecommendedModel])
async def get_recommended_models():
    models = {
        "llama3.2:3b": {...},
        "llama3.1:8b": {...},
        # ...
    }
    # ❌ return models  # Retourne un dict
    # ✅ return list(models.values())  # Retourne une liste
    return [
        RecommendedModel(name=name, **data)
        for name, data in models.items()
    ]
```

**Priorité** : Moyenne (non-bloquant, les modèles Ollama fonctionnent autrement)

---

## 📊 Matrice de Priorités

| # | Problème | Priorité | Impact | Blocant | Effort |
|---|----------|----------|--------|---------|--------|
| 1 | Sélecteur de dossier ne s'ouvre pas | ⚠️ **CRITIQUE** | Tous les utilisateurs | ✅ OUI | 1h |
| 2 | Validation de dossier échoue | ⚠️ **CRITIQUE** | Tous les utilisateurs | ✅ OUI | 2h |
| 3 | Absence de sélecteur de langue | 🔶 **HAUTE** | Utilisateurs anglophones | ❌ NON | 2h |
| 4 | Erreur Ollama recommended | 🟡 **MOYENNE** | Utilisateurs Ollama | ❌ NON | 30min |

---

## 🗓️ Plan de Correction Recommandé

### Jour 1 (5h) - Déblocage Critique
- **Matin (3h)** :
  - Problème #1 : Fixer le sélecteur de dossier (1h)
  - Problème #2 : Fixer la validation de dossier (2h)
  - Tests intensifs du workflow complet (1h)

- **Après-midi (2h)** :
  - Problème #3 : Implémenter le sélecteur de langue (2h)
  - Tests de changement de langue (30min)

### Jour 2 (2h) - Polissage
- Problème #4 : Fixer l'erreur Ollama (30min)
- Tests E2E complets (1h)
- Préparation release v2.0.1 (30min)

---

## ✅ Checklist de Validation Complète

### Test du Workflow Complet

- [ ] **Lancement**
  - [ ] L'application démarre sans erreur
  - [ ] Les logs ne montrent aucune erreur critique
  - [ ] Le backend Python démarre correctement

- [ ] **Langue**
  - [ ] Sélecteur de langue visible sur la page d'accueil
  - [ ] Changement FR → EN fonctionne
  - [ ] Changement EN → FR fonctionne
  - [ ] La langue est sauvegardée après redémarrage

- [ ] **Wizard - Étape Dossier**
  - [ ] Bouton "Parcourir" ouvre le sélecteur de dossier
  - [ ] Sélection d'un dossier valide affiche le chemin
  - [ ] Saisie manuelle d'un chemin valide fonctionne
  - [ ] Validation affiche les statistiques (fichiers, taille, extensions)
  - [ ] Tentative avec un dossier vide affiche une erreur
  - [ ] Tentative avec un chemin invalide affiche une erreur
  - [ ] Bouton "Continuer" activé uniquement si validation OK

- [ ] **Wizard - Complétion**
  - [ ] Toutes les étapes sont complétables
  - [ ] La base de connaissances est créée à la fin
  - [ ] Redirection vers la page "Knowledge Bases"
  - [ ] La nouvelle KB apparaît dans la liste

---

## 📁 Fichiers à Modifier (Résumé)

### Priorité CRITIQUE
1. ✅ `desktop/src/lib/ipc.ts` (lignes 259-273)
2. ✅ `ragkit/desktop/main.py` ou `app.py` (router mounting)
3. ✅ `desktop/src-tauri/src/commands.rs` (ligne 241+)

### Priorité HAUTE
4. ✅ **NOUVEAU** : `desktop/src/components/LanguageSelector.tsx`
5. ✅ `desktop/src/pages/Wizard/WelcomeStep.tsx`
6. ✅ `desktop/src/pages/Settings.tsx`
7. ✅ `desktop/src/locales/fr.json`
8. ✅ `desktop/src/locales/en.json`

### Priorité MOYENNE
9. ✅ `ragkit/desktop/ollama_api.py` (ou équivalent)

---

## 🔎 Commandes de Diagnostic Utiles

### Vérifier l'état du backend
```bash
curl http://127.0.0.1:8100/health
curl -X POST http://127.0.0.1:8100/api/wizard/validate-folder \
  -H "Content-Type: application/json" \
  -d '{"folder_path": "C:\\Users\\henri\\Projets\\ragkit"}'
```

### Analyser les logs en temps réel
```bash
# Windows PowerShell
Get-Content "C:\Users\henri\.ragkit\logs\ragkit-desktop.log.*" -Tail 50 -Wait

# Git Bash / WSL
tail -f "C:\Users\henri\.ragkit\logs\ragkit-desktop.log."*
```

### Chercher les erreurs dans les logs
```bash
grep -n "ERROR\|Failed\|404\|500" "C:\Users\henri\.ragkit\logs\ragkit-desktop.log."*
```

---

## 📞 Notes pour le Développeur

### Points d'Attention

1. **Import dynamique Tauri** : Éviter les `await import()` pour les plugins Tauri en production. Toujours utiliser des imports statiques.

2. **Router FastAPI** : Vérifier systématiquement que tous les routers sont montés dans l'application principale avec le bon préfixe `/api`.

3. **Validation d'erreurs** : Ajouter des logs explicites dans les blocs try/catch pour faciliter le débogage :
   ```typescript
   } catch (err) {
     console.error("Detailed error:", err);
     console.error("Error stack:", err instanceof Error ? err.stack : "N/A");
     setError(t("wizard.folder.validation.browseFailed"));
   }
   ```

4. **Tests de build production** : Toujours tester avec `npm run tauri:build` et l'exécutable final, pas seulement en mode dev.

### Questions à Clarifier

- [ ] Le fichier principal de l'API backend est-il `main.py` ou `app.py` ?
- [ ] Y a-t-il un fichier de configuration Tauri (`tauri.conf.json`) qui pourrait interférer avec les permissions de dialogue ?
- [ ] Les permissions de sécurité Windows bloquent-elles les dialogues natifs ?

---

**Document généré le** : 11 février 2026
**Basé sur** : Analyse des logs, inspection du code source, et captures d'écran fournies par l'utilisateur
**Prochaine étape** : Correction des problèmes critiques #1 et #2 en priorité absolue

