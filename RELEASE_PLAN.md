# Plan d'implémentation - Releases binaires RAGKIT Desktop

## Objectif
Publier des releases binaires de RAGKIT Desktop pour Windows, macOS et Linux sur GitHub Releases, permettant aux utilisateurs d'installer l'application sans avoir à compiler depuis le code source.

---

## Prérequis

### Outils et environnements
- **Node.js 18+** et npm
- **Rust** et Cargo (version stable récente)
- **Tauri CLI** : `npm install -g @tauri-apps/cli`
- **Python 3.11+** avec le projet installé (`pip install -e .`)
- **Accès GitHub** : permissions de créer des releases sur le dépôt

### Systèmes de build
Pour créer des releases multi-plateformes, besoin d'accès à :
- **Windows** : Windows 10/11 avec Visual Studio Build Tools
- **macOS** : macOS avec Xcode Command Line Tools
- **Linux** : Ubuntu 20.04+ ou Debian

**Alternative recommandée** : Utiliser GitHub Actions pour automatiser les builds multi-plateformes

---

## Étapes d'implémentation

### 1. Préparer le projet Tauri

#### 1.1 Vérifier la configuration Tauri
**Fichier** : `desktop/src-tauri/tauri.conf.json`

**Actions** :
- Vérifier que `productName` est défini : `"RAGKIT Desktop"`
- Vérifier `identifier` : doit être unique (ex: `com.ragkit.desktop`)
- Vérifier `version` : correspond à la version à publier (ex: `"0.1.0"`)
- Vérifier la section `bundle` :
  ```json
  "bundle": {
    "active": true,
    "targets": ["msi", "nsis", "deb", "appimage", "dmg"],
    "identifier": "com.ragkit.desktop",
    "icon": [
      "icons/32x32.png",
      "icons/128x128.png",
      "icons/128x128@2x.png",
      "icons/icon.icns",
      "icons/icon.ico"
    ]
  }
  ```

#### 1.2 Vérifier/créer les icônes
**Dossier** : `desktop/src-tauri/icons/`

**Actions** :
- Vérifier la présence de toutes les icônes requises :
  - `icon.ico` (Windows)
  - `icon.icns` (macOS)
  - `32x32.png`, `128x128.png`, `128x128@2x.png`, `icon.png` (Linux)
- Si manquantes : générer depuis une icône source avec `tauri icon` ou un outil comme ImageMagick

#### 1.3 Configurer l'updater (optionnel pour v1)
**Fichier** : `desktop/src-tauri/tauri.conf.json`

**Actions** :
- Pour l'instant, désactiver l'updater automatique :
  ```json
  "updater": {
    "active": false
  }
  ```
- Prévoir de l'activer dans une version future avec signature des releases

---

### 2. Tester les builds locaux

#### 2.1 Build de développement
**Commandes** :
```bash
cd desktop
npm install
npm run tauri dev
```

**Vérifications** :
- L'application se lance correctement
- Toutes les fonctionnalités sont accessibles
- Pas d'erreurs critiques dans les logs

#### 2.2 Build de production local
**Commandes** :
```bash
cd desktop
npm run tauri build
```

**Résultats attendus** :
- **Windows** : `.exe` et `.msi` dans `desktop/src-tauri/target/release/bundle/`
- **macOS** : `.dmg` et `.app` dans `desktop/src-tauri/target/release/bundle/`
- **Linux** : `.AppImage` et `.deb` dans `desktop/src-tauri/target/release/bundle/`

**Tests** :
- Installer le package sur le système local
- Vérifier que l'application se lance
- Tester les fonctionnalités principales :
  - Création d'une base de connaissances
  - Ajout de documents
  - Requêtes RAG
  - Gestion des conversations
  - Configuration des clés API

---

### 3. Automatiser avec GitHub Actions

#### 3.1 Créer le workflow de release
**Fichier à créer** : `.github/workflows/release.yml`

**Contenu** :
```yaml
name: Release RAGKIT Desktop

on:
  push:
    tags:
      - 'v*.*.*'  # Déclenché sur les tags de version (ex: v0.1.0)

jobs:
  build-desktop:
    strategy:
      fail-fast: false
      matrix:
        platform: [ubuntu-20.04, windows-latest, macos-latest]

    runs-on: ${{ matrix.platform }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'

      - name: Setup Rust
        uses: dtolnay/rust-toolchain@stable

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Python dependencies
        run: pip install -e .

      - name: Install desktop dependencies
        run: |
          cd desktop
          npm install

      - name: Build Tauri app
        run: |
          cd desktop
          npm run tauri build

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: desktop-${{ matrix.platform }}
          path: |
            desktop/src-tauri/target/release/bundle/**/*.exe
            desktop/src-tauri/target/release/bundle/**/*.msi
            desktop/src-tauri/target/release/bundle/**/*.dmg
            desktop/src-tauri/target/release/bundle/**/*.AppImage
            desktop/src-tauri/target/release/bundle/**/*.deb

  create-release:
    needs: build-desktop
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Download all artifacts
        uses: actions/download-artifact@v4

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          files: |
            desktop-*/**/*
          draft: false
          prerelease: false
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

#### 3.2 Tester le workflow
**Actions** :
1. Créer une branche de test
2. Pousser le workflow
3. Créer un tag de test : `git tag v0.1.0-alpha && git push origin v0.1.0-alpha`
4. Vérifier que le workflow se déclenche dans l'onglet Actions
5. Corriger les erreurs éventuelles
6. Supprimer le tag de test : `git tag -d v0.1.0-alpha && git push origin :refs/tags/v0.1.0-alpha`

---

### 4. Préparer la release notes

#### 4.1 Créer un template de release notes
**Fichier à créer** : `.github/RELEASE_TEMPLATE.md`

**Contenu** :
```markdown
# RAGKIT Desktop v{VERSION}

## 🎉 Nouveautés
- [Lister les nouvelles fonctionnalités]

## 🐛 Corrections
- [Lister les bugs corrigés]

## 📦 Installation

### Windows
1. Télécharger `RAGKIT-Desktop_{VERSION}_x64-setup.exe` ou `.msi`
2. Lancer l'installeur et suivre les instructions

### macOS
1. Télécharger `RAGKIT-Desktop_{VERSION}_x64.dmg` (Intel) ou `_aarch64.dmg` (Apple Silicon)
2. Ouvrir le `.dmg` et glisser l'app dans Applications
3. Au premier lancement : clic droit > Ouvrir

### Linux
**AppImage** :
```bash
chmod +x RAGKIT-Desktop_{VERSION}_amd64.AppImage
./RAGKIT-Desktop_{VERSION}_amd64.AppImage
```

**Debian/Ubuntu** :
```bash
sudo dpkg -i RAGKIT-Desktop_{VERSION}_amd64.deb
```

## 🚀 Démarrage rapide

### Avec Ollama (recommandé pour débutants)
1. Installer Ollama : https://ollama.ai/
2. Lancer RAGKIT Desktop
3. L'application télécharge automatiquement les modèles

### Avec providers cloud
1. Obtenir une clé API (OpenAI, Anthropic, etc.)
2. Ouvrir Settings dans RAGKIT Desktop
3. Configurer le provider et entrer la clé API

## 📚 Documentation
- Guide d'installation complet : [INSTALL.md](../INSTALL.md)
- Documentation : [README.md](../README.md)

## ⚠️ Notes importantes
- Première release : peut contenir des bugs
- Données stockées localement dans `~/.ragkit/`
- Rapporter les bugs sur : https://github.com/henribesnard/ragkit/issues
```

---

### 5. Créer et publier la première release

#### 5.1 Préparer le code
**Actions** :
1. S'assurer que tous les bugs critiques sont corrigés
2. Mettre à jour `desktop/src-tauri/Cargo.toml` avec la version : `version = "0.1.0"`
3. Mettre à jour `desktop/src-tauri/tauri.conf.json` avec la version
4. Mettre à jour `desktop/package.json` avec la version
5. Créer un commit de version : `git commit -am "Prepare release v0.1.0"`

#### 5.2 Créer le tag
**Commandes** :
```bash
git tag -a v0.1.0 -m "Release v0.1.0 - First stable release"
git push origin v0.1.0
```

#### 5.3 Surveiller le workflow
**Actions** :
1. Aller sur GitHub > Actions
2. Vérifier que le workflow `Release RAGKIT Desktop` se lance
3. Attendre la fin du build (peut prendre 15-30 minutes)
4. Vérifier les logs en cas d'erreur

#### 5.4 Finaliser la release
**Actions** :
1. Aller sur GitHub > Releases
2. La release devrait être créée automatiquement
3. Éditer la release :
   - Copier le contenu du template de release notes
   - Remplacer `{VERSION}` par `0.1.0`
   - Ajouter les changements spécifiques
4. Vérifier que tous les binaires sont attachés :
   - Windows : `.exe` et `.msi`
   - macOS : `.dmg` (x64 et aarch64)
   - Linux : `.AppImage` et `.deb`
5. Publier la release

---

### 6. Mettre à jour la documentation

#### 6.1 Mettre à jour INSTALL.md
**Fichier** : `INSTALL.md`

**Actions** :
- Supprimer l'avertissement "Les releases binaires ne sont pas encore disponibles"
- Déplacer la section "Installation depuis le code source" en bas
- Mettre en avant l'installation depuis les releases

#### 6.2 Mettre à jour README.md
**Fichier** : `README.md`

**Actions** :
- Ajouter un badge de release :
  ```markdown
  [![Release](https://img.shields.io/github/v/release/henribesnard/ragkit)](https://github.com/henribesnard/ragkit/releases/latest)
  ```
- Ajouter un lien vers les releases dans la section installation
- Mettre à jour les screenshots si l'UI a changé

---

### 7. Tests post-release

#### 7.1 Tests manuels
**Sur chaque plateforme** :
1. Télécharger le binaire depuis GitHub Releases
2. Installer l'application
3. Lancer et vérifier :
   - Démarrage sans erreur
   - Création d'une KB
   - Ajout de documents (PDF, DOCX, TXT)
   - Ingestion et indexation
   - Requêtes RAG fonctionnelles
   - Historique des conversations
   - Configuration des providers

#### 7.2 Tests automatisés (optionnel pour v1)
**À implémenter plus tard** :
- Tests end-to-end avec Playwright ou Selenium
- Tests d'installation automatisés
- Tests de mise à jour

---

## Problèmes potentiels et solutions

### Problème 1 : Taille excessive des binaires
**Cause** : Bundle incluant trop de dépendances ou fichiers inutiles

**Solutions** :
- Optimiser les dépendances dans `package.json` (dev vs prod)
- Exclure les fichiers inutiles dans `.taurignore`
- Utiliser la compression dans la config Tauri

### Problème 2 : Erreurs de signature sur macOS
**Cause** : macOS requiert la signature des apps

**Solutions** :
- Pour tests : l'utilisateur doit faire "clic droit > Ouvrir"
- Pour production : obtenir un certificat Apple Developer (99$/an)
- Configurer la signature dans GitHub Actions secrets

### Problème 3 : Antivirus bloquant l'app sur Windows
**Cause** : Binaire non signé détecté comme suspect

**Solutions** :
- Court terme : ajouter une note dans INSTALL.md
- Long terme : obtenir un certificat de signature de code Windows
- Alternative : publier sur Microsoft Store

### Problème 4 : Backend Python non trouvé
**Cause** : Le backend Python n'est pas correctement bundlé

**Solutions** :
- Vérifier la configuration Tauri pour inclure le backend
- Utiliser PyInstaller ou cx_Freeze pour bundler le backend
- Documenter l'installation de Python si requis

### Problème 5 : Permissions manquantes sur Linux
**Cause** : AppImage ou .deb sans permissions d'exécution

**Solutions** :
- Documenter le `chmod +x` pour AppImage
- Vérifier les permissions dans le workflow de build
- Ajouter des post-install scripts pour .deb

---

## Checklist de lancement

### Avant le lancement
- [ ] Tous les bugs CRITIQUE et HAUT sont corrigés (voir CODE_REVIEW.md)
- [ ] Tests manuels passés sur les 3 plateformes
- [ ] Documentation à jour (README, INSTALL, CHANGELOG)
- [ ] Icônes et assets finalisés
- [ ] Workflow GitHub Actions testé
- [ ] Release notes préparées

### Lancement
- [ ] Version mise à jour dans tous les fichiers
- [ ] Commit de version créé
- [ ] Tag créé et poussé
- [ ] Workflow exécuté avec succès
- [ ] Binaires vérifiés et testés
- [ ] Release publiée sur GitHub
- [ ] Documentation mise à jour

### Après le lancement
- [ ] Annonce sur les réseaux sociaux / forums
- [ ] Monitoring des issues GitHub
- [ ] Réponse aux premiers utilisateurs
- [ ] Planification de la v0.2.0

---

## Estimation des délais

| Tâche | Temps estimé |
|-------|-------------|
| Configuration Tauri et icônes | 2-4h |
| Tests locaux et corrections | 4-8h |
| Configuration GitHub Actions | 3-6h |
| Tests du workflow | 2-4h |
| Préparation release notes | 1-2h |
| Tests post-release | 3-5h |
| Documentation | 2-3h |
| **TOTAL** | **17-32h** |

---

## Recommandations

### Pour la v0.1.0
1. **Commencer petit** : Release alpha/beta d'abord
2. **Tester intensivement** : Trouver les bugs avant les utilisateurs
3. **Documentation claire** : Les utilisateurs doivent comprendre comment installer
4. **Support actif** : Être réactif sur les issues GitHub

### Pour les futures versions
1. **Automatisation** : Tests automatisés + déploiement continu
2. **Signature** : Obtenir les certificats pour Windows et macOS
3. **Auto-update** : Implémenter le système de mise à jour Tauri
4. **Analytics** : Collecter des métriques d'usage (opt-in)
5. **Distribution** : Microsoft Store, Homebrew, APT repository

---

## Ressources utiles

- [Tauri Bundle Documentation](https://tauri.app/v1/guides/building/)
- [GitHub Actions Tauri Action](https://github.com/tauri-apps/tauri-action)
- [Code Signing Guide](https://tauri.app/v1/guides/distribution/sign-macos)
- [Windows Code Signing](https://tauri.app/v1/guides/distribution/sign-windows)

---

## Contact / Questions

Pour toute question sur ce plan d'implémentation :
- Ouvrir une issue GitHub
- Consulter la documentation Tauri
- Demander sur le Discord Tauri
