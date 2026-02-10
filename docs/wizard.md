# Wizard de configuration RAGKIT

Ce document décrit le wizard de configuration initiale (phase 1), côté backend et frontend.

## Objectif

Le wizard guide l'utilisateur en 5 étapes pour générer une configuration par défaut adaptée à son cas d'usage, puis enregistre les réglages essentiels (embedding, LLM, chunking, retrieval).

## Parcours utilisateur

1. **Bienvenue** : présentation de RAGKIT et du processus.
2. **Profilage** : questions pour identifier le type de base et les contraintes.
3. **Modèles** : choix des providers et des modèles (avec détection GPU/Ollama).
4. **Dossier** : sélection du répertoire de documents.
5. **Résumé** : validation avant sauvegarde des paramètres.

## Endpoints API (backend)

Base path : `/api/wizard`

- `POST /analyze-profile`
  - Analyse les réponses et retourne le profil recommandé.
  - Payload :
    - `kb_type`
    - `has_tables_diagrams`
    - `needs_multi_document`
    - `large_documents`
    - `needs_precision`
    - `frequent_updates`
    - `cite_page_numbers`

- `GET /environment-detection`
  - Détecte le GPU et l'état d'Ollama.

## Composants frontend

- `desktop/src/pages/Wizard/index.tsx` (orchestrateur)
- `desktop/src/pages/Wizard/WelcomeStep.tsx`
- `desktop/src/pages/Wizard/ProfileStep.tsx`
- `desktop/src/pages/Wizard/ModelsStep.tsx`
- `desktop/src/pages/Wizard/FolderStep.tsx`
- `desktop/src/pages/Wizard/SummaryStep.tsx`

Le wizard est monté via `desktop/src/pages/Onboarding.tsx`.

## Exemple de flux d’intégration

1. L’utilisateur répond au questionnaire.
2. Le frontend appelle `/api/wizard/analyze-profile`.
3. Le profil recommandé est affiché et utilisé pour préremplir les réglages.
4. Le frontend enregistre les settings via `ipc.updateSettings`.

## Notes

- Les profils sont définis dans `ragkit/config/profiles.py`.
- La logique d’analyse est dans `ragkit/config/wizard.py`.
- La détection hardware est dans `ragkit/utils/hardware.py`.
