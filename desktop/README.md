# RAGKIT Desktop - Guide d'Installation et d'Utilisation

## Table des Matières

1. [Prérequis](#prérequis)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Utilisation](#utilisation)
5. [Dépannage](#dépannage)

---

## Prérequis

### Système d'exploitation
- **Windows** 10/11 (x64)
- **macOS** 12+ (Intel ou Apple Silicon)
- **Linux** Ubuntu 22.04+ ou équivalent (x64)

### Logiciels requis

#### Pour le développement / build depuis les sources :
- **Node.js** 20+ ([télécharger](https://nodejs.org/))
- **Rust** 1.70+ ([télécharger](https://rustup.rs/))
- **Python** 3.10+ ([télécharger](https://python.org/))

#### Dépendances système (Linux uniquement) :
```bash
sudo apt-get update
sudo apt-get install -y \
  libwebkit2gtk-4.1-dev \
  libappindicator3-dev \
  librsvg2-dev \
  patchelf \
  libssl-dev \
  libgtk-3-dev
```

#### Optionnel (pour LLM local) :
- **Ollama** ([télécharger](https://ollama.ai/)) - Pour l'inférence LLM locale

---

## Installation

### Option 1 : Télécharger les binaires (recommandé)

> **Note** : Les binaires pré-compilés seront disponibles dans les [Releases GitHub](https://github.com/henribesnard/ragkit/releases) une fois la phase Alpha terminée.

1. Téléchargez le fichier correspondant à votre OS :
   - Windows : `ragkit-desktop-windows-x64.msi` ou `.exe`
   - macOS : `ragkit-desktop-macos-x64.dmg` ou `ragkit-desktop-macos-arm64.dmg`
   - Linux : `ragkit-desktop-linux-x64.AppImage` ou `.deb`

2. Installez selon votre système :
   - **Windows** : Double-cliquez sur le `.msi` ou `.exe`
   - **macOS** : Ouvrez le `.dmg` et glissez l'app dans Applications
   - **Linux** : Rendez l'AppImage exécutable (`chmod +x *.AppImage`) ou installez le `.deb`

### Option 2 : Build depuis les sources

#### 1. Cloner le dépôt
```bash
git clone https://github.com/henribesnard/ragkit.git
cd ragkit
```

#### 2. Installer les dépendances Python
```bash
# Créer un environnement virtuel (recommandé)
python -m venv .venv

# Activer l'environnement
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Installer les dépendances desktop
pip install -e ".[desktop]"
```

#### 3. Installer les dépendances frontend
```bash
cd desktop
npm install
```

#### 4. Lancer en mode développement
```bash
# Depuis le dossier desktop/
npm run tauri:dev
```

#### 5. Build pour production
```bash
# Depuis le dossier desktop/
npm run tauri:build
```

Les binaires seront générés dans `desktop/src-tauri/target/release/bundle/`.

---

## Configuration

### Premier lancement (Onboarding)

Au premier lancement, un assistant de configuration vous guidera :

#### Étape 1 : Bienvenue
- Présentation de l'application
- Cliquez sur "Commencer"

#### Étape 2 : Choix du mode
Choisissez entre :

| Mode | Description | Prérequis |
|------|-------------|-----------|
| **100% Local** | Tout fonctionne hors-ligne | Ollama installé |
| **Cloud** | Utilise des APIs cloud | Clés API (OpenAI, Anthropic...) |
| **Hybride** | Embeddings locaux + LLM cloud | Optionnel |

#### Étape 3 : Configuration Embeddings

**Option A : ONNX Local (recommandé pour confidentialité)**
- Aucune configuration requise
- Le modèle `all-MiniLM-L6-v2` sera téléchargé automatiquement (~90 MB)
- Fonctionne 100% hors-ligne

**Option B : OpenAI**
- Requiert une clé API OpenAI
- Modèles : `text-embedding-3-small` ou `text-embedding-3-large`

**Option C : Ollama**
- Requiert Ollama en cours d'exécution
- Modèles : `nomic-embed-text`, `mxbai-embed-large`

#### Étape 4 : Configuration LLM

**Option A : Ollama (recommandé pour local)**
1. Installez Ollama depuis [ollama.ai](https://ollama.ai)
2. Téléchargez un modèle :
   ```bash
   ollama pull llama3.2:3b    # Rapide, 2 GB
   ollama pull llama3.1:8b    # Qualité, 5 GB
   ollama pull mistral:7b     # Équilibré, 4 GB
   ```
3. Dans l'app, sélectionnez le modèle téléchargé

**Option B : OpenAI**
- Entrez votre clé API OpenAI
- Modèles : `gpt-4o-mini` (économique) ou `gpt-4o` (qualité)

**Option C : Anthropic**
- Entrez votre clé API Anthropic
- Modèles : `claude-3-haiku` (rapide) ou `claude-3.5-sonnet` (qualité)

#### Étape 5 : Création première base de connaissances
- Donnez un nom à votre base
- Sélectionnez un dossier de documents à indexer
- Formats supportés : PDF, TXT, MD, DOCX

### Configuration avancée (Settings)

Après l'onboarding, accédez aux paramètres via l'icône ⚙️ :

#### Changer de provider
1. Allez dans **Settings**
2. Modifiez **Embedding Model** ou **Language Model**
3. Cliquez sur **Save**

#### Gérer les clés API
1. Allez dans **Settings > API Keys**
2. Cliquez sur **Add** ou **Update** pour chaque provider
3. Les clés sont stockées de façon sécurisée dans le trousseau système

#### Gérer Ollama
Si vous utilisez Ollama :
1. L'indicateur de status apparaît dans Settings
2. **Vert** = En cours d'exécution
3. **Jaune** = Installé mais arrêté (cliquez "Start")
4. **Rouge** = Non installé (cliquez pour instructions)

---

## Utilisation

### Créer une base de connaissances

1. Cliquez sur **Knowledge Bases** dans la barre latérale
2. Cliquez sur **+ Create**
3. Remplissez :
   - **Name** : Nom de la base (ex: "Documentation Projet")
   - **Description** : Description optionnelle
4. Cliquez sur **Create**

### Ajouter des documents

1. Sélectionnez une base de connaissances
2. Cliquez sur **Add Documents**
3. Sélectionnez les fichiers (PDF, TXT, MD, DOCX)
4. Attendez l'indexation (barre de progression)

**Formats supportés :**
| Format | Extension | Notes |
|--------|-----------|-------|
| PDF | `.pdf` | Texte et images OCR |
| Text | `.txt` | Texte brut |
| Markdown | `.md` | Avec formatage |
| Word | `.docx` | Documents Office |

### Poser des questions

1. Cliquez sur **Chat** dans la barre latérale
2. Sélectionnez une base de connaissances dans le menu déroulant
3. Tapez votre question
4. Appuyez sur Entrée ou cliquez sur l'icône d'envoi

**Fonctionnalités du chat :**
- **Sources** : Cliquez sur "X sources" pour voir les extraits utilisés
- **Score** : Chaque source affiche un score de pertinence (vert = excellent)
- **Latence** : Le temps de réponse est affiché sous chaque réponse

### Gérer les conversations

- Les conversations sont automatiquement sauvegardées
- Créez une nouvelle conversation en rechargeant la page
- L'historique complet est préservé entre les sessions

---

## Dépannage

### L'application ne démarre pas

**Windows :**
```
Erreur : "WebView2 Runtime not found"
```
→ Installez [WebView2 Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/)

**macOS :**
```
Erreur : "App is damaged and can't be opened"
```
→ Exécutez : `xattr -cr /Applications/RAGKIT\ Desktop.app`

**Linux :**
```
Erreur : libwebkit2gtk-4.1 not found
```
→ Installez les dépendances système (voir Prérequis)

### Le backend ne répond pas

1. Vérifiez que Python est installé : `python --version`
2. Vérifiez les logs dans la console développeur (F12)
3. Redémarrez l'application

### Ollama ne fonctionne pas

1. Vérifiez qu'Ollama est installé : `ollama --version`
2. Démarrez le service : `ollama serve`
3. Vérifiez qu'un modèle est installé : `ollama list`
4. Téléchargez un modèle si nécessaire : `ollama pull llama3.2:3b`

### Les embeddings sont lents

**ONNX Local :**
- Premier lancement = téléchargement du modèle (~90 MB)
- Les embeddings suivants sont mis en cache

**Solutions :**
1. Utilisez un modèle plus petit (`all-MiniLM-L6-v2`)
2. Réduisez la taille des documents
3. Utilisez un provider cloud pour les gros volumes

### Erreur "API Key Invalid"

1. Vérifiez que la clé est correctement copiée (sans espaces)
2. Vérifiez que le provider correspond à la clé
3. Vérifiez votre quota/facturation sur le dashboard du provider

### Messages d'erreur courants

| Erreur | Cause | Solution |
|--------|-------|----------|
| "Connection refused" | Backend non démarré | Redémarrez l'app |
| "Model not found" | Modèle Ollama manquant | `ollama pull <model>` |
| "Rate limited" | Trop de requêtes API | Attendez ou upgradez |
| "Context too long" | Conversation trop longue | Nouvelle conversation |

---

## Support

- **Issues GitHub** : [github.com/henribesnard/ragkit/issues](https://github.com/henribesnard/ragkit/issues)
- **Documentation** : Voir `RAGKIT_DESKTOP_SPECS.md`
- **Roadmap** : Voir `RAGKIT_DESKTOP_ROADMAP.md`

---

## Raccourcis clavier

| Action | Windows/Linux | macOS |
|--------|---------------|-------|
| Nouvelle conversation | `Ctrl+N` | `Cmd+N` |
| Envoyer message | `Enter` | `Enter` |
| Paramètres | `Ctrl+,` | `Cmd+,` |
| Fermer modal | `Escape` | `Escape` |

---

## Versions

- **Version actuelle** : 1.5.0 (Alpha)
- **Python requis** : 3.10+
- **Node.js requis** : 20+
- **Rust requis** : 1.70+
