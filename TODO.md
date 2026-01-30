# RAGKIT - Corrections restantes

Deux items identifis lors de la revue de code du 30/01/2026 restent a traiter.

---

## 1. FRONT-01 : Builder le frontend et deployer dans `ragkit/ui/dist/`

**Priorite** : Haute
**Statut** : ✅ Terminé
**Contexte** : Le code source React existe dans `ragkit-ui/src/` mais le dossier `ragkit/ui/dist/` est vide (seul un `.gitkeep` est present). FastAPI verifie l'existence de ce dossier au demarrage (`ragkit/api/app.py:64-66`) pour servir le SPA. Sans le build, la Web UI n'est jamais accessible via `ragkit serve --with-ui`.

### Etapes

1. Installer les dependances frontend :

```bash
cd ragkit-ui
npm install
```

2. Verifier que le build passe (TypeScript + Vite) :

```bash
npx tsc --noEmit
npm run build
```

3. Copier le build dans le package Python :

```bash
# La commande CLI fait deja ca :
ragkit ui build

# Ou manuellement :
rm -rf ragkit/ui/dist
cp -r ragkit-ui/dist ragkit/ui/dist
```

4. Verifier que le serveur sert bien le frontend :

```bash
ragkit serve --with-ui --config ragkit-v1-config.yaml
# Ouvrir http://localhost:8000 dans le navigateur
```

### Notes

- Le CI (`.github/workflows/ci.yml`, job `frontend`) fait deja `npm ci && npx tsc --noEmit && npm run build` mais ne copie pas le build dans `ragkit/ui/dist/`. Si on veut que le package publie inclue le frontend, il faut ajouter cette copie dans le workflow ou dans le `setup.py`/`pyproject.toml`.
- `zod` et `react-hook-form` ont ete retires de `package.json`. Il faut re-generer le lockfile avec `npm install` avant de builder.

---

## 2. BACK-06 : Ajouter des tests pour le CLI (`ragkit/cli/main.py`)

**Priorite** : Moyenne
**Statut** : ✅ Terminé (tests ajoutés dans `tests/integration/test_cli.py`)
**Contexte** : Les 7 commandes CLI (`init`, `validate`, `ingest`, `query`, `serve`, `ui build`, `ui dev`) n'ont aucun test. Les deux bugs critiques (BUG-01 `embedder_doc` non defini, BUG-02 echappement invalide) auraient ete detectes par un test basique du `serve`.

### Fichier a creer

`tests/integration/test_cli.py`

### Commandes a tester

| Commande | Strategie de test |
|----------|-------------------|
| `ragkit init <name>` | Verifier que le dossier est cree avec `ragkit.yaml` et `data/documents/` |
| `ragkit validate -c <config>` | Verifier que la validation passe pour `ragkit-v1-config.yaml` et echoue pour un YAML invalide |
| `ragkit ingest` | Mocker l'embedder et le vector store, verifier que le pipeline s'execute |
| `ragkit query` | Mocker l'orchestrateur complet, verifier que la reponse est affichee |
| `ragkit serve` | Verifier que l'app FastAPI est creee sans crash (ne pas demarrer uvicorn) |
| `ragkit ui build` | Verifier le comportement quand `ragkit-ui/` n'existe pas |
| `ragkit ui dev` | Verifier le comportement quand `ragkit-ui/` n'existe pas |

### Exemple de squelette

```python
"""Tests for ragkit CLI commands."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from ragkit.cli.main import app

runner = CliRunner()


def test_init_creates_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "my-project", "--template", "minimal"])
    assert result.exit_code == 0
    assert (tmp_path / "my-project" / "ragkit.yaml").exists()
    assert (tmp_path / "my-project" / "data" / "documents").exists()


def test_init_fails_if_exists(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "existing").mkdir()
    result = runner.invoke(app, ["init", "existing"])
    assert result.exit_code != 0


def test_validate_valid_config():
    result = runner.invoke(app, ["validate", "-c", "ragkit-v1-config.yaml"])
    assert result.exit_code == 0
    assert "OK" in result.stdout


def test_validate_invalid_config(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("invalid: [yaml")
    result = runner.invoke(app, ["validate", "-c", str(bad)])
    assert result.exit_code != 0
```

### Dependances

- `typer.testing.CliRunner` est deja disponible via `typer` (dependance existante).
- Les tests de `ingest`, `query`, et `serve` necessitent de mocker les composants externes (embedder, vector store, LLM) pour eviter les appels reseau. Utiliser `monkeypatch` ou `unittest.mock.patch` sur les factory functions (`create_embedder`, `create_vector_store`, etc.).
- Les helpers partages sont disponibles dans `tests/helpers.py` (`DummyEmbedder`, `DummyVectorStore`, `DummyLLM`, etc.).
