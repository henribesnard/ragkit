# 🧰 Ragkit — Parcours Utilisateur Idéal

> **Version** : 1.0  
> **Objectif** : Définir le parcours utilisateur complet de Ragkit, de l'installation au chat opérationnel, en garantissant une expérience fluide, moderne et autonome.

---

## Vue d'ensemble du parcours

Le parcours se décompose en **6 phases principales**, présentées à l'utilisateur sous forme d'un assistant de configuration (wizard) avec une barre de progression visuelle.

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  1. Install  │───▶│ 2. Bienvenue │───▶│  3. Profil   │
│   & Launch   │    │  & Présenta. │    │    de base   │
└──────────────┘    └──────────────┘    └──────┬───────┘
                                               │
┌──────────────┐    ┌──────────────┐    ┌──────▼───────┐
│ 6. Dashboard │◀───│  5. Base de  │◀───│ 4. Config.   │
│   & Chat     │    │ connaissances│    │   Modèles    │
└──────────────┘    └──────────────┘    └──────────────┘
```

---

## Phase 1 — Installation & Lancement

### 1.1 Distribution

- L'utilisateur télécharge un **installeur `.exe`** (Windows) signé numériquement.
- L'installeur crée un dossier dédié `C:\Users\<user>\AppData\Local\Ragkit\` contenant :
  - Le binaire de l'application
  - Un sous-dossier `models/` pour les modèles locaux
  - Un sous-dossier `data/` pour les index et bases vectorielles
  - Un sous-dossier `config/` pour les fichiers de configuration (chiffrés)
  - Un sous-dossier `logs/` pour les journaux d'activité

### 1.2 Premier lancement

- L'application s'ouvre et détecte qu'aucune configuration n'existe → déclenchement automatique du **wizard de configuration**.
- Si une configuration existe déjà → accès direct au **dashboard** (Phase 6).

---

## Phase 2 — Écran de bienvenue

### 2.1 Message d'accueil

L'écran affiche :

> **Bienvenue dans Ragkit 👋**
>
> Ragkit est votre assistant RAG (Retrieval-Augmented Generation) local et privé. Il vous permet de :
>
> - **Ingérer** vos documents (PDF, Word, Markdown, TXT, HTML, CSV…)
> - **Interroger** votre base de connaissances en langage naturel
> - **Obtenir des réponses** sourcées et précises, avec citations
>
> Ragkit fonctionne entièrement en local ou via des API cloud, selon votre choix. Vos données restent sous votre contrôle.

### 2.2 Bouton d'action

- **[ Commencer la configuration →]**

### 2.3 Détail supplémentaire (lien dépliable)

- Lien "En savoir plus" ouvrant un panneau avec : architecture simplifiée, modèles supportés, types de fichiers pris en charge.

---

## Phase 3 — Profilage de la base de connaissances

### 3.1 Objectif

Proposer une **configuration par défaut optimisée** en fonction du type de base de connaissances, sans demander à l'utilisateur de comprendre les paramètres techniques.

### 3.2 Question principale

> **Quel type de contenu décrit le mieux votre base de connaissances ?**

| Option | Description |
|--------|-------------|
| 📘 Documentation technique | Manuels, spécifications, guides d'architecture |
| ❓ FAQ / Support | Questions-réponses, articles d'aide, tickets |
| 📜 Juridique / Réglementaire | Contrats, textes de loi, procédures de conformité |
| 📊 Rapports & Analyses | Rapports financiers, études, bilans |
| 📚 Base généraliste | Mélange de contenus variés |

### 3.3 Questions de calibrage (Oui / Non)

Ces questions permettent d'affiner le profil et de déterminer les paramètres par défaut (taille de chunks, overlap, stratégie de retrieval, etc.).

| # | Question | Impact si OUI |
|---|----------|---------------|
| 1 | Vos documents contiennent-ils des **tableaux ou schémas** ? | Active le parsing avancé (tables, OCR) |
| 2 | Les réponses attendues nécessitent-elles de **croiser plusieurs documents** ? | Active le multi-document retrieval, augmente `top_k` |
| 3 | Vos documents font-ils en moyenne **plus de 50 pages** ? | Augmente la taille des chunks, active le chunking hiérarchique |
| 4 | Avez-vous besoin de réponses **très précises** (chiffres, dates, références exactes) ? | Active le reranking, réduit la température du LLM |
| 5 | Votre base sera-t-elle **mise à jour fréquemment** (ajout/suppression de documents) ? | Active le mode watch sur le répertoire |
| 6 | Souhaitez-vous que les réponses citent les **sources et numéros de page** ? | Active le suivi des métadonnées de source |

### 3.4 Résultat

L'application affiche un récapitulatif du profil détecté :

> **Profil détecté : Documentation technique avancée**
>
> - Chunking : hiérarchique (512 tokens, overlap 64)
> - Retrieval : hybrid (BM25 + sémantique), top_k = 8
> - Reranking : activé
> - Parsing : tableaux et OCR activés
> - Sources : citations avec numéro de page
>
> *Vous pourrez modifier tous ces paramètres ultérieurement dans les réglages avancés.*

Boutons : **[ Accepter et continuer → ]** | **[ Modifier manuellement ]**

---

## Phase 4 — Configuration des modèles

### 4.1 Détection automatique de l'environnement

L'application exécute **automatiquement** les vérifications suivantes (avec indicateur de progression) :

```
✅ Détection GPU : NVIDIA RTX 3060 (12 Go VRAM)
🔍 Recherche d'Ollama...
✅ Ollama détecté (v0.3.12) — 2 modèles installés
   ├── llama3.1:8b
   └── nomic-embed-text
```

### 4.2 Arbre de décision des modèles

```
Ollama détecté ?
├── OUI → Proposer d'utiliser les modèles Ollama existants
│         + proposer d'en télécharger d'autres via Ollama
│         + proposer aussi l'option API cloud
│
└── NON → L'utilisateur souhaite-t-il utiliser des modèles locaux ?
          ├── OUI → Deux options :
          │         ├── A) Installer Ollama (lien + guide)
          │         └── B) Modèles intégrés Ragkit (téléchargement
          │              depuis Hugging Face, gérés par l'application)
          └── NON → Configuration API cloud uniquement
```

### 4.3 Option A — Modèles via Ollama

Si Ollama est présent ou installé :

- L'application liste les modèles disponibles localement.
- Elle propose les modèles recommandés manquants avec un bouton **[ Installer via Ollama ]**.
- Modèles recommandés selon le profil :
  - **Embedding** : `nomic-embed-text`, `mxbai-embed-large`
  - **LLM** : `llama3.1:8b`, `mistral:7b`, `qwen2.5:7b`
  - **Reranking** : géré par Ragkit directement (voir 4.5)

### 4.4 Option B — Modèles intégrés Ragkit (sans Ollama)

Ragkit peut télécharger et gérer ses propres modèles depuis Hugging Face, stockés dans `Ragkit/models/`. L'application ne supporte que des modèles qu'elle sait gérer nativement :

**Modèles intégrés supportés :**

| Catégorie | Modèle | Taille | VRAM min. |
|-----------|--------|--------|-----------|
| Embedding | `BAAI/bge-small-en-v1.5` | ~130 Mo | 1 Go |
| Embedding | `BAAI/bge-base-en-v1.5` | ~440 Mo | 2 Go |
| Embedding | `intfloat/multilingual-e5-large` | ~2.2 Go | 4 Go |
| LLM (GGUF) | `TheBloke/Mistral-7B-Instruct-v0.2-GGUF` (Q4) | ~4 Go | 6 Go |
| LLM (GGUF) | `TheBloke/Llama-2-7B-Chat-GGUF` (Q4) | ~4 Go | 6 Go |

- L'application indique clairement la VRAM disponible et recommande les modèles compatibles.
- Téléchargement avec **barre de progression** et possibilité de **mettre en pause / reprendre**.
- Avertissement clair : *"Ces modèles seront gérés par Ragkit indépendamment d'Ollama."*

### 4.5 Modèles de reranking

Les modèles de reranking sont **toujours gérés par Ragkit** (pas par Ollama), téléchargés depuis Hugging Face et stockés dans `Ragkit/models/rerankers/`.

**Modèles disponibles :**

| Modèle | Taille | Langue |
|--------|--------|--------|
| `BAAI/bge-reranker-v2-m3` | ~2.2 Go | Multilingue |
| `cross-encoder/ms-marco-MiniLM-L-6-v2` | ~90 Mo | Anglais |

- Le modèle recommandé est présélectionné selon le profil (Phase 3).
- L'installation se fait automatiquement en arrière-plan avec confirmation utilisateur.

### 4.6 Option C — API Cloud

Si l'utilisateur choisit les API cloud (ou en complément du local) :

> **Configurez vos clés API**
>
> Ragkit a besoin des clés suivantes selon votre configuration :

| Service | Clé requise | Usage |
|---------|-------------|-------|
| OpenAI | `sk-...` | LLM (GPT-4o, GPT-4o-mini) et/ou Embeddings |
| Anthropic | `sk-ant-...` | LLM (Claude 3.5 Sonnet, Claude 3 Haiku) |
| Cohere | `...` | Reranking (Cohere Rerank) |
| Mistral AI | `...` | LLM et/ou Embeddings |
| Voyage AI | `...` | Embeddings spécialisés |

- Les clés sont **stockées chiffrées** dans `Ragkit/config/credentials.enc` (chiffrement AES-256 avec clé dérivée de la machine).
- Un bouton **[ Tester la connexion ]** valide chaque clé en temps réel.
- L'utilisateur peut combiner local + cloud (ex. : embeddings locaux + LLM via API).

### 4.7 Récapitulatif de la configuration modèles

```
╔══════════════════════════════════════════╗
║        Configuration des modèles         ║
╠══════════════════════════════════════════╣
║ Embedding  : nomic-embed-text (Ollama)   ║
║ LLM        : GPT-4o-mini (API OpenAI) ✅║
║ Reranker   : bge-reranker-v2-m3 (local)  ║
║ GPU        : RTX 3060 — 8.2/12 Go libre  ║
╚══════════════════════════════════════════╝
```

Boutons : **[ Confirmer → ]** | **[ Modifier ]**

---

## Phase 5 — Configuration de la base de connaissances

### 5.1 Sélection du répertoire

> **Où se trouvent vos documents ?**
>
> Sélectionnez le dossier contenant votre base de connaissances.

- Bouton **[ Parcourir… ]** ouvrant un sélecteur de dossier natif.
- Possibilité de **glisser-déposer** un dossier.
- Chemin affiché avec validation : `D:\Documents\Base_Technique\`

### 5.2 Analyse automatique du répertoire

L'application scanne le répertoire et affiche un rapport :

```
📂 Analyse de D:\Documents\Base_Technique\

📊 Statistiques globales :
   ├── 347 fichiers détectés
   ├── Taille totale : 1.2 Go
   └── 12 sous-dossiers

📄 Types de fichiers :
   ├── PDF          : 198 fichiers (842 Mo)
   ├── DOCX         :  67 fichiers (215 Mo)
   ├── Markdown     :  45 fichiers  (12 Mo)
   ├── TXT          :  22 fichiers   (3 Mo)
   ├── HTML         :  11 fichiers   (8 Mo)
   ├── CSV          :   4 fichiers (120 Mo)
   └── ⚠️ Non supportés : 3 fichiers (.exe, .zip) — seront ignorés

📁 Sous-dossiers :
   ├── /Architecture/        (45 fichiers)
   ├── /API-Reference/       (89 fichiers)
   ├── /Guides-Utilisateur/  (67 fichiers)
   ├── /FAQ/                 (32 fichiers)
   ├── /Archives-2022/       (78 fichiers)
   └── /Divers/              (36 fichiers)
```

### 5.3 Sélection des sous-dossiers

> **Quels dossiers souhaitez-vous inclure dans la base de connaissances ?**

- **[ ✅ Tout sélectionner ]** — sélectionné par défaut
- Ou sélection individuelle avec cases à cocher :

```
☑ /Architecture/          (45 fichiers)
☑ /API-Reference/         (89 fichiers)
☑ /Guides-Utilisateur/    (67 fichiers)
☑ /FAQ/                   (32 fichiers)
☐ /Archives-2022/         (78 fichiers)  ← décoché par l'utilisateur
☑ /Divers/                (36 fichiers)
```

- Compteur dynamique : **269 fichiers sélectionnés sur 347** — estimation : ~15 min d'ingestion.

### 5.4 Options supplémentaires (dépliable)

- **[ ] Activer le mode watch** : surveiller le répertoire et ingérer automatiquement les nouveaux fichiers.
- **[ ] Ignorer les fichiers de plus de __ Mo** : filtre de taille.
- **[ ] Patterns d'exclusion** : ex. `*_draft.*`, `*_old.*`

Bouton : **[ Lancer l'ingestion → ]**

---

## Phase 6 — Dashboard & Utilisation

### 6.1 Tableau de bord principal

Le dashboard est l'écran principal une fois la configuration terminée. Il est divisé en zones claires :

```
┌─────────────────────────────────────────────────────────────┐
│  🧰 Ragkit                          ⚙️ Paramètres  📋 Logs │
├─────────────────────┬───────────────────────────────────────┤
│                     │                                       │
│   ÉTAT DES SERVICES │          ZONE PRINCIPALE              │
│                     │                                       │
│  Embedding  🟢 OK   │   ┌─────────────────────────────┐    │
│  LLM        🟢 OK   │   │                             │    │
│  Reranker   🟢 OK   │   │        💬 CHAT RAG          │    │
│  Vector DB  🟢 OK   │   │                             │    │
│                     │   │  (ou statut d'ingestion     │    │
│  ─────────────────  │   │   si en cours)              │    │
│                     │   │                             │    │
│  INGESTION          │   └─────────────────────────────┘    │
│  📊 269/269 docs    │                                       │
│  ✅ Terminée        │   Temps de réponse moy. : 2.3s       │
│                     │   Documents pertinents moy. : 4.2     │
│  CHAT               │                                       │
│  🟢 Disponible      │                                       │
│                     │                                       │
│  ─────────────────  │                                       │
│  Base : 269 docs    │                                       │
│  Index : 12,847     │                                       │
│  chunks             │                                       │
│  Dernière MAJ :     │                                       │
│  10/02/2026 14:32   │                                       │
│                     │                                       │
└─────────────────────┴───────────────────────────────────────┘
```

### 6.2 États des services

Chaque service affiche un indicateur en temps réel :

| Indicateur | Signification |
|------------|---------------|
| 🟢 OK | Service opérationnel |
| 🟡 Chargement | Service en cours de démarrage |
| 🔴 Erreur | Service indisponible (cliquer pour détails) |
| ⚪ Désactivé | Service non configuré |

### 6.3 Statut du chat

- **Indisponible** tant que l'ingestion est en cours (avec barre de progression et estimation du temps restant).
- **Disponible** dès que l'ingestion est terminée et que tous les services requis sont opérationnels.
- Si l'ingestion est longue, possibilité d'activer un **mode partiel** : le chat devient disponible après l'ingestion des N premiers documents, et continue l'ingestion en arrière-plan.

### 6.4 Panneau d'ingestion (pendant l'ingestion)

```
📥 Ingestion en cours...

[████████████████░░░░░░░░░░] 67% — 180/269 documents

⏱️ Temps écoulé : 8 min 12 s
⏳ Temps restant estimé : ~4 min

📄 En cours : Guide_Architecture_v3.pdf (page 42/128)

Détails :
├── ✅ Réussis    : 178
├── ⚠️ Avertiss. :   2  (fichiers partiellement lus)
└── ❌ Échecs    :   0

[ ⏸️ Pause ]  [ ❌ Annuler ]
```

---

## Phase 7 — Paramètres

### 7.1 Paramètres généraux

Accessibles à tout moment via l'icône ⚙️. Modifications qui **ne nécessitent PAS** de réingestion :

| Paramètre | Description | Défaut |
|-----------|-------------|--------|
| Modèle LLM | Changer le modèle de génération | Selon config initiale |
| Température | Créativité des réponses (0.0 → 1.0) | 0.1 |
| Langue de réponse | Langue préférée pour les réponses | Français |
| Nombre de sources affichées | Sources citées dans chaque réponse | 3 |
| Prompt système | Personnaliser les instructions du LLM | Prompt par défaut |
| Mode watch | Surveiller le répertoire pour les nouveaux fichiers | Selon profil |
| Thème | Clair / Sombre / Système | Système |
| Export de configuration | Exporter / Importer un fichier `.ragkit-config` | — |

### 7.2 Paramètres avancés

Modifications qui **déclenchent une réingestion** (partielle ou totale). L'application avertit l'utilisateur avant d'appliquer :

> ⚠️ **Attention** : Modifier ce paramètre nécessite une réingestion complète de la base de connaissances. Cela prendra environ 15 minutes. Souhaitez-vous continuer ?

| Paramètre | Description | Déclencheur |
|-----------|-------------|-------------|
| Modèle d'embedding | Changer le modèle vectoriel | Réingestion **totale** |
| Taille des chunks | Taille des fragments de texte | Réingestion **totale** |
| Overlap des chunks | Chevauchement entre fragments | Réingestion **totale** |
| Stratégie de chunking | Par paragraphe / fixe / sémantique / hiérarchique | Réingestion **totale** |
| Modèle de reranking | Changer le modèle de reclassement | Pas de réingestion |
| Top K retrieval | Nombre de chunks récupérés | Pas de réingestion |
| Stratégie de retrieval | Sémantique / BM25 / Hybride | Réingestion **partielle** (index BM25) |
| Dossiers inclus | Ajouter/retirer des sous-dossiers | Réingestion **incrémentale** |
| Patterns d'exclusion | Filtres de fichiers | Réingestion **incrémentale** |

### 7.3 Indicateur visuel de réingestion

Quand un paramètre avancé est modifié, un bandeau s'affiche sur le dashboard :

```
🔄 Réingestion nécessaire — Paramètre modifié : taille des chunks (256 → 512)
   [ Relancer maintenant ]  [ Reporter ]
```

Si l'utilisateur reporte, le chat reste disponible avec l'ancien index, et un badge d'avertissement rappelle que la configuration n'est pas à jour.

---

## Phase 8 — Interface de chat

### 8.1 Fonctionnalités du chat

- **Zone de saisie** avec support du multilignes.
- **Réponses streamées** (affichage token par token en temps réel).
- **Sources citées** sous chaque réponse, cliquables pour voir l'extrait exact du document.
- **Bouton de copie** pour chaque réponse.
- **Historique des conversations** avec possibilité de créer plusieurs sessions.
- **Indicateur de confiance** : score de pertinence des sources retrouvées.

### 8.2 Exemple d'interaction

```
👤 Utilisateur :
   Comment configurer l'authentification SSO dans notre API Gateway ?

🤖 Ragkit :
   Pour configurer l'authentification SSO dans l'API Gateway, vous devez
   suivre les étapes suivantes :

   1. Accédez au fichier de configuration `gateway.yml` et ajoutez le
      bloc `sso_provider` avec les paramètres de votre fournisseur
      d'identité (SAML ou OIDC)...

   [Réponse complète]

   ──────────────────────────────────────
   📎 Sources :
   ├── 📄 Guide_API_Gateway_v3.pdf — p.47-49  [Pertinence : 94%]
   ├── 📄 SSO_Integration_Notes.md — §3.2      [Pertinence : 87%]
   └── 📄 FAQ_Authentification.docx — Q12       [Pertinence : 72%]
```

### 8.3 Question de validation (post-ingestion)

À la première utilisation du chat après une ingestion, Ragkit propose automatiquement :

> 💡 **Testez votre base de connaissances !**
>
> Ragkit a généré une question de test basée sur vos documents. Voulez-vous l'essayer ?
>
> **[ Essayer la question test ]** | **[ Passer ]**

Cela permet à l'utilisateur de valider immédiatement que le système fonctionne correctement.

---

## Gestion des logs

Accessible via l'icône 📋 sur le dashboard.

```
📋 Logs Ragkit

[Filtre : Tous ▾]  [Niveau : Info ▾]  [Rechercher...]

2026-02-10 14:32:01 [INFO]  Ingestion terminée — 269 documents, 12847 chunks
2026-02-10 14:31:45 [WARN]  Fichier partiellement lu : rapport_2019.pdf (pages 45-47 illisibles)
2026-02-10 14:28:12 [INFO]  Modèle de reranking chargé : bge-reranker-v2-m3
2026-02-10 14:27:03 [INFO]  Connexion Ollama établie
2026-02-10 14:27:01 [INFO]  Démarrage de Ragkit v1.0.0

[ Exporter les logs ]  [ Effacer ]
```

---

## Résumé du flux complet

```
Installation .exe
       │
       ▼
Écran de bienvenue
       │
       ▼
Profilage de la base ──── Questions Oui/Non ──── Profil détecté
       │
       ▼
Détection environnement
       │
       ├── Ollama trouvé ─────── Config modèles Ollama
       │
       ├── Pas Ollama + Local ── Installer Ollama
       │                         OU Modèles intégrés Ragkit (HuggingFace)
       │
       └── API Cloud ─────────── Saisie clés API (chiffrées)
       │
       ▼
Reranker (toujours géré par Ragkit / HuggingFace)
       │
       ▼
Sélection répertoire ──── Analyse automatique ──── Sélection sous-dossiers
       │
       ▼
Ingestion (avec progression)
       │
       ├── En cours ──── Chat indisponible (+ option mode partiel)
       │
       └── Terminée ──── Chat disponible + Question test proposée
       │
       ▼
Dashboard opérationnel
       │
       ├── Chat RAG avec sources
       ├── Paramètres généraux (sans réingestion)
       ├── Paramètres avancés (avec réingestion si nécessaire)
       ├── Logs et diagnostics
       └── Mode watch (optionnel)
```

---

## Améliorations futures envisageables

| Priorité | Fonctionnalité | Description |
|----------|---------------|-------------|
| 🔴 Haute | Multi-bases | Gérer plusieurs bases de connaissances distinctes |
| 🔴 Haute | Mise à jour incrémentale | Ne réingérer que les fichiers modifiés |
| 🟡 Moyenne | Export de conversations | Exporter les sessions de chat en PDF/Markdown |
| 🟡 Moyenne | Plugins de parsing | Support de formats additionnels (EPUB, PPTX, XLS) |
| 🟢 Basse | Mode multi-utilisateur | Authentification et bases séparées par utilisateur |
| 🟢 Basse | API REST | Exposer le chat RAG via une API pour intégrations tierces |
| 🟢 Basse | Évaluation automatique | Métriques de qualité du RAG (faithfulness, relevancy) |
