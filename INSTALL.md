# RAGKIT Desktop - Guide d'installation et d'utilisation

## État actuel

⚠️ **Les releases binaires ne sont pas encore disponibles.**

Pour l'instant, l'installation se fait depuis le code source. Des releases binaires seront publiées prochainement sur :
https://github.com/henribesnard/ragkit/releases

---

## Installation depuis le code source

### Prérequis

- Python 3.11 ou supérieur
- Node.js 18+ et npm
- Rust et Cargo (pour Tauri)

### Étapes

1. **Cloner le dépôt**
```bash
git clone https://github.com/henribesnard/ragkit.git
cd ragkit
```

2. **Installer les dépendances Python**
```bash
pip install -e .
```

3. **Construire et lancer le desktop**
```bash
cd desktop
npm install
npm run tauri dev
```

---

## Installer (une fois les releases disponibles)

### Windows

1. Lancer le fichier `.exe` ou `.msi` telecharge
2. Suivre l'assistant d'installation
3. L'application est disponible dans le menu Demarrer

### macOS

1. Ouvrir le fichier `.dmg`
2. Glisser RAGKIT Desktop dans le dossier Applications
3. Au premier lancement, faire clic droit > Ouvrir (securite macOS)

### Linux

**AppImage :**
```bash
chmod +x RAGKIT-Desktop_*.AppImage
./RAGKIT-Desktop_*.AppImage
```

**Debian/Ubuntu :**
```bash
sudo dpkg -i RAGKIT-Desktop_*.deb
```

---

## Premier lancement

Au premier lancement, l'application est prete a l'emploi avec les parametres par defaut.

Deux options pour le moteur d'IA :

### Option A : Modeles locaux avec Ollama (gratuit, aucune cle API)

1. Installer Ollama depuis https://ollama.ai/
2. Lancer RAGKIT Desktop
3. L'application detecte Ollama automatiquement et telecharge les modeles necessaires

### Option B : Providers cloud (OpenAI, Anthropic, etc.)

1. Lancer RAGKIT Desktop
2. Aller dans **Settings**
3. Choisir le provider LLM souhaite
4. Entrer votre cle API
5. Selectionner le modele

| Provider | Cle API | Site |
|----------|---------|------|
| OpenAI | Requise | https://platform.openai.com/api-keys |
| Anthropic | Requise | https://console.anthropic.com/ |
| DeepSeek | Requise | https://platform.deepseek.com/ |
| Groq | Requise | https://console.groq.com/ |
| Mistral | Requise | https://console.mistral.ai/ |
| Ollama | Non | https://ollama.ai/ |

---

## Utilisation

### Creer une base de connaissances

1. Cliquer sur **Knowledge Bases** dans le menu
2. Cliquer sur **Create**
3. Donner un nom a la base
4. Cliquer sur **Add Documents** et selectionner vos fichiers (PDF, Word, TXT, Markdown)
5. L'indexation demarre automatiquement

### Poser des questions

1. Cliquer sur **Chat** dans le menu
2. Selectionner la base de connaissances a interroger
3. Taper votre question et appuyer sur Entree
4. La reponse est generee a partir du contenu de vos documents

### Gerer les conversations

- Les conversations sont sauvegardees automatiquement
- Retrouvez l'historique dans le panneau lateral
- Supprimez une conversation avec le bouton de suppression

---

## Donnees

Toutes vos donnees restent sur votre ordinateur :

- **Base de donnees** : parametres, bases de connaissances, historique des conversations
- **Index vectoriels** : contenu indexe de vos documents
- **Cles API** : stockees dans le gestionnaire de credentials de votre systeme (Credential Manager sur Windows, Trousseau sur macOS)

Pour reinitialiser l'application, supprimer le dossier `~/.ragkit/` dans votre repertoire utilisateur.

---

## Desinstaller

### Windows
Panneau de configuration > Programmes > Desinstaller RAGKIT Desktop

### macOS
Glisser RAGKIT Desktop du dossier Applications vers la corbeille

### Linux
```bash
# AppImage : supprimer le fichier
# Debian/Ubuntu :
sudo apt remove ragkit-desktop
```

Pour supprimer aussi les donnees : supprimer le dossier `~/.ragkit/`.
