# Plan Complet RAGKIT v2.0
## Système RAG Professionnel avec Configuration Exhaustive

**Version**: 2.0
**Date**: 2026-02-10
**Objectif**: Transformer RAGKIT en solution RAG professionnelle de niveau entreprise avec tous les paramètres configurables

---

## 📊 Vue d'ensemble

Ce plan implémente **150+ paramètres RAG** répartis en **12 phases** avec des tests unitaires à chaque étape. L'objectif est de créer une solution complète et professionnelle qui offre une configuration fine tout en restant accessible aux utilisateurs via un wizard intelligent.

### Principes directeurs

1. **Configuration progressive** : L'utilisateur commence simple (wizard), puis accède aux paramètres avancés
2. **Valeurs par défaut intelligentes** : Profilage automatique selon le type de base de connaissances
3. **Testabilité** : Tests unitaires et end-to-end à chaque phase
4. **Performance** : Optimisations de cache et batch processing
5. **Observabilité** : Logs, métriques et monitoring complets

---

## 📋 Table des matières

1. [Phase 1: Infrastructure & Wizard](#phase-1-infrastructure--wizard)
2. [Phase 2: Ingestion & Parsing Avancé](#phase-2-ingestion--parsing-avancé)
3. [Phase 3: Chunking Avancé](#phase-3-chunking-avancé)
4. [Phase 4: Embedding & Vector DB](#phase-4-embedding--vector-db)
5. [Phase 5: Retrieval Multi-stratégies](#phase-5-retrieval-multi-stratégies)
6. [Phase 6: Reranking & Optimisation](#phase-6-reranking--optimisation)
7. [Phase 7: LLM & Génération](#phase-7-llm--génération)
8. [Phase 8: Cache & Performance](#phase-8-cache--performance)
9. [Phase 9: Monitoring & Evaluation](#phase-9-monitoring--evaluation)
10. [Phase 10: Security & Compliance](#phase-10-security--compliance)
11. [Phase 11: UI/UX Complète](#phase-11-uiux-complète)
12. [Phase 12: Tests End-to-End](#phase-12-tests-end-to-end)

---

## Phase 1: Infrastructure & Wizard

**Objectif**: Créer la base architecturale et le wizard de configuration initiale

**État**: [ ] En cours | [ ] À tester | [ ] Testé | [x] Terminé

### 1.1 Architecture Backend

**Fichiers à créer/modifier**:
- `ragkit/config/schema_v2.py` - Schéma Pydantic complet avec TOUS les paramètres
- `ragkit/config/profiles.py` - Profils prédéfinis par type de base
- `ragkit/config/wizard.py` - Logique du wizard
- `ragkit/desktop/wizard_api.py` - API du wizard pour le frontend

**Paramètres à implémenter**:

```python
# ragkit/config/schema_v2.py

class WizardProfileConfig(BaseModel):
    """Configuration détectée par le wizard."""

    # Type de base de connaissances
    knowledge_base_type: Literal[
        "technical_documentation",
        "faq_support",
        "legal_regulatory",
        "reports_analysis",
        "general_knowledge"
    ]

    # Questions de calibrage (Oui/Non)
    has_tables_diagrams: bool = False
    needs_multi_document: bool = False
    large_documents: bool = False  # >50 pages
    needs_precision: bool = False  # Chiffres, dates exactes
    frequent_updates: bool = False
    cite_page_numbers: bool = False

    # Résultat du profil
    detected_profile_name: str
    recommended_config: dict[str, Any]
```

**Schéma de profils**:

```python
# ragkit/config/profiles.py

PROFILES = {
    "technical_documentation": {
        "chunking": {
            "strategy": "semantic",
            "chunk_size": 512,
            "chunk_overlap": 64,
        },
        "retrieval": {
            "architecture": "hybrid",
            "alpha": 0.3,  # Favorise lexical
            "top_k": 10,
        },
        "reranking": {
            "enabled": True,
        },
        "parsing": {
            "table_extraction": True,
            "ocr_enabled": False,
        },
    },
    "faq_support": {
        "chunking": {
            "strategy": "paragraph_based",
            "chunk_size": 256,
            "chunk_overlap": 50,
        },
        "retrieval": {
            "architecture": "hybrid",
            "alpha": 0.8,  # Favorise sémantique
            "top_k": 5,
        },
        "reranking": {
            "enabled": False,
        },
    },
    # ... autres profils
}

def get_profile_for_answers(
    kb_type: str,
    has_tables: bool,
    needs_multi_doc: bool,
    large_docs: bool,
    needs_precision: bool,
    frequent_updates: bool,
    cite_pages: bool,
) -> dict:
    """Génère un profil personnalisé selon les réponses."""
    base_profile = PROFILES[kb_type].copy()

    # Ajustements selon les réponses
    if has_tables:
        base_profile["parsing"]["table_extraction"] = True
        base_profile["parsing"]["header_detection"] = True

    if needs_multi_doc:
        base_profile["retrieval"]["top_k"] = max(
            base_profile["retrieval"]["top_k"], 15
        )

    if large_docs:
        base_profile["chunking"]["chunk_size"] = 1024
        base_profile["chunking"]["chunk_overlap"] = 128
        base_profile["chunking"]["strategy"] = "recursive"

    if needs_precision:
        base_profile["reranking"]["enabled"] = True
        base_profile["llm"]["temperature"] = 0.0
        base_profile["retrieval"]["top_k"] += 5

    if frequent_updates:
        base_profile["maintenance"]["incremental_indexing"] = True
        base_profile["maintenance"]["auto_refresh_interval"] = 3600  # 1h

    if cite_pages:
        base_profile["metadata"]["add_page_numbers"] = True
        base_profile["llm"]["cite_sources"] = True
        base_profile["llm"]["citation_format"] = "footnote"

    return base_profile
```

### 1.2 API Wizard Backend

**Fichier**: `ragkit/desktop/wizard_api.py`

```python
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/wizard")

class WizardAnswersRequest(BaseModel):
    kb_type: str
    has_tables_diagrams: bool
    needs_multi_document: bool
    large_documents: bool
    needs_precision: bool
    frequent_updates: bool
    cite_page_numbers: bool

class WizardProfileResponse(BaseModel):
    profile_name: str
    description: str
    config_summary: dict
    full_config: dict

@router.post("/analyze-profile")
async def analyze_profile(
    answers: WizardAnswersRequest
) -> WizardProfileResponse:
    """Analyse les réponses et retourne le profil recommandé."""
    from ragkit.config.profiles import get_profile_for_answers

    profile = get_profile_for_answers(
        kb_type=answers.kb_type,
        has_tables=answers.has_tables_diagrams,
        needs_multi_doc=answers.needs_multi_document,
        large_docs=answers.large_documents,
        needs_precision=answers.needs_precision,
        frequent_updates=answers.frequent_updates,
        cite_pages=answers.cite_page_numbers,
    )

    # Générer description
    description = _generate_profile_description(profile)

    # Générer résumé lisible
    summary = {
        "chunking": f"{profile['chunking']['strategy']} "
                   f"({profile['chunking']['chunk_size']} tokens, "
                   f"overlap {profile['chunking']['chunk_overlap']})",
        "retrieval": f"{profile['retrieval']['architecture']} "
                    f"(top_k = {profile['retrieval']['top_k']})",
        "reranking": "activé" if profile['reranking']['enabled'] else "désactivé",
        "parsing": "tableaux + OCR" if profile['parsing'].get('table_extraction') else "standard",
    }

    return WizardProfileResponse(
        profile_name=_get_profile_name(answers.kb_type, profile),
        description=description,
        config_summary=summary,
        full_config=profile,
    )

@router.get("/environment-detection")
async def detect_environment():
    """Détecte l'environnement (GPU, Ollama, etc.)."""
    from ragkit.utils.hardware import detect_gpu, detect_ollama

    gpu_info = detect_gpu()
    ollama_status = await detect_ollama()

    return {
        "gpu": {
            "detected": gpu_info.detected,
            "name": gpu_info.name,
            "vram_total_gb": gpu_info.vram_total_gb,
            "vram_free_gb": gpu_info.vram_free_gb,
        },
        "ollama": {
            "installed": ollama_status.installed,
            "running": ollama_status.running,
            "version": ollama_status.version,
            "models": ollama_status.models,
        },
    }
```

### 1.3 Frontend Wizard (React)

**Fichiers à créer**:
- `desktop/src/pages/Wizard/index.tsx` - Page principale du wizard
- `desktop/src/pages/Wizard/WelcomeStep.tsx` - Étape bienvenue
- `desktop/src/pages/Wizard/ProfileStep.tsx` - Étape profilage
- `desktop/src/pages/Wizard/ModelsStep.tsx` - Étape configuration modèles
- `desktop/src/pages/Wizard/FolderStep.tsx` - Étape sélection dossier
- `desktop/src/pages/Wizard/SummaryStep.tsx` - Récapitulatif

**Composant principal**:

```typescript
// desktop/src/pages/Wizard/index.tsx

import { useState } from "react";
import { WelcomeStep } from "./WelcomeStep";
import { ProfileStep } from "./ProfileStep";
import { ModelsStep } from "./ModelsStep";
import { FolderStep } from "./FolderStep";
import { SummaryStep } from "./SummaryStep";

type WizardStep = "welcome" | "profile" | "models" | "folder" | "summary";

export function Wizard() {
  const [currentStep, setCurrentStep] = useState<WizardStep>("welcome");
  const [wizardData, setWizardData] = useState({
    profile: null,
    models: null,
    folder: null,
  });

  const steps: WizardStep[] = ["welcome", "profile", "models", "folder", "summary"];
  const currentStepIndex = steps.indexOf(currentStep);
  const progress = ((currentStepIndex + 1) / steps.length) * 100;

  return (
    <div className="h-full flex flex-col">
      {/* Barre de progression */}
      <div className="h-2 bg-gray-200 dark:bg-gray-700">
        <div
          className="h-full bg-primary-600 transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Indicateur d'étapes */}
      <div className="px-6 py-4 border-b">
        <div className="flex justify-between max-w-4xl mx-auto">
          {["Bienvenue", "Profil", "Modèles", "Dossiers", "Résumé"].map((label, idx) => (
            <div
              key={label}
              className={`flex items-center ${
                idx <= currentStepIndex ? "text-primary-600" : "text-gray-400"
              }`}
            >
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  idx <= currentStepIndex
                    ? "bg-primary-600 text-white"
                    : "bg-gray-200 text-gray-500"
                }`}
              >
                {idx + 1}
              </div>
              <span className="ml-2 hidden sm:inline">{label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Contenu de l'étape */}
      <div className="flex-1 overflow-auto">
        {currentStep === "welcome" && (
          <WelcomeStep onNext={() => setCurrentStep("profile")} />
        )}
        {currentStep === "profile" && (
          <ProfileStep
            onNext={(profile) => {
              setWizardData({ ...wizardData, profile });
              setCurrentStep("models");
            }}
            onBack={() => setCurrentStep("welcome")}
          />
        )}
        {currentStep === "models" && (
          <ModelsStep
            profile={wizardData.profile}
            onNext={(models) => {
              setWizardData({ ...wizardData, models });
              setCurrentStep("folder");
            }}
            onBack={() => setCurrentStep("profile")}
          />
        )}
        {currentStep === "folder" && (
          <FolderStep
            onNext={(folder) => {
              setWizardData({ ...wizardData, folder });
              setCurrentStep("summary");
            }}
            onBack={() => setCurrentStep("models")}
          />
        )}
        {currentStep === "summary" && (
          <SummaryStep
            wizardData={wizardData}
            onConfirm={() => {
              // Lancer la configuration
            }}
            onBack={() => setCurrentStep("folder")}
          />
        )}
      </div>
    </div>
  );
}
```

### 1.4 Tests Unitaires Phase 1

**Fichier**: `tests/test_wizard.py`

```python
import pytest
from ragkit.config.profiles import get_profile_for_answers, PROFILES

class TestWizardProfiles:
    """Tests pour la génération de profils."""

    def test_technical_documentation_base_profile(self):
        """Test du profil technique de base."""
        profile = get_profile_for_answers(
            kb_type="technical_documentation",
            has_tables=False,
            needs_multi_doc=False,
            large_docs=False,
            needs_precision=False,
            frequent_updates=False,
            cite_pages=False,
        )

        assert profile["chunking"]["strategy"] == "semantic"
        assert profile["chunking"]["chunk_size"] == 512
        assert profile["retrieval"]["alpha"] == 0.3
        assert profile["reranking"]["enabled"] is True

    def test_profile_with_large_documents(self):
        """Test avec documents > 50 pages."""
        profile = get_profile_for_answers(
            kb_type="technical_documentation",
            has_tables=False,
            needs_multi_doc=False,
            large_docs=True,  # Documents longs
            needs_precision=False,
            frequent_updates=False,
            cite_pages=False,
        )

        assert profile["chunking"]["chunk_size"] == 1024
        assert profile["chunking"]["chunk_overlap"] == 128
        assert profile["chunking"]["strategy"] == "recursive"

    def test_profile_with_precision_requirement(self):
        """Test avec besoin de précision."""
        profile = get_profile_for_answers(
            kb_type="legal_regulatory",
            has_tables=False,
            needs_multi_doc=False,
            large_docs=False,
            needs_precision=True,  # Précision requise
            frequent_updates=False,
            cite_pages=True,
        )

        assert profile["reranking"]["enabled"] is True
        assert profile["llm"]["temperature"] == 0.0
        assert profile["llm"]["cite_sources"] is True
        assert profile["metadata"]["add_page_numbers"] is True

    def test_profile_with_frequent_updates(self):
        """Test avec mises à jour fréquentes."""
        profile = get_profile_for_answers(
            kb_type="faq_support",
            has_tables=False,
            needs_multi_doc=False,
            large_docs=False,
            needs_precision=False,
            frequent_updates=True,  # MAJ fréquentes
            cite_pages=False,
        )

        assert profile["maintenance"]["incremental_indexing"] is True
        assert profile["maintenance"]["auto_refresh_interval"] == 3600


class TestWizardAPI:
    """Tests pour l'API du wizard."""

    @pytest.mark.asyncio
    async def test_analyze_profile_endpoint(self, client):
        """Test de l'endpoint d'analyse de profil."""
        response = await client.post(
            "/api/wizard/analyze-profile",
            json={
                "kb_type": "technical_documentation",
                "has_tables_diagrams": True,
                "needs_multi_document": True,
                "large_documents": False,
                "needs_precision": True,
                "frequent_updates": False,
                "cite_page_numbers": True,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "profile_name" in data
        assert "description" in data
        assert "config_summary" in data
        assert "full_config" in data

        # Vérifier les ajustements
        config = data["full_config"]
        assert config["parsing"]["table_extraction"] is True
        assert config["retrieval"]["top_k"] >= 15  # Multi-doc
        assert config["reranking"]["enabled"] is True  # Précision
```

---

## Phase 2: Ingestion & Parsing Avancé

**Objectif**: Implémenter tous les paramètres d'ingestion et de parsing

**État**: [ ] En cours | [ ] À tester | [ ] Testé | [ ] Terminé

### 2.1 Document Parsing Avancé

**Paramètres à implémenter** (voir `parametres_rag_exhaustif.md` section 1.1):

```python
# ragkit/config/schema_v2.py

class DocumentParsingConfig(BaseModel):
    """Configuration complète du parsing."""

    # Loaders
    document_loader_type: Literal[
        "auto",  # Détection automatique
        "pdf",
        "docx",
        "html",
        "markdown",
        "txt",
        "csv",
        "json",
        "xml",
    ] = "auto"

    # OCR
    ocr_enabled: bool = False
    ocr_language: list[str] = ["fra", "eng"]
    ocr_engine: Literal["tesseract", "easyocr", "doctr"] = "tesseract"
    ocr_dpi: int = 300
    ocr_preprocessing: bool = True  # Amélioration d'image

    # Tableaux
    table_extraction_strategy: Literal[
        "none",
        "preserve",  # Préserve la structure
        "markdown",  # Convertit en markdown
        "separate",  # Extrait dans chunks séparés
        "vision",  # Utilise vision model
    ] = "preserve"
    table_detection_threshold: float = 0.8

    # Images
    image_captioning_enabled: bool = False
    image_captioning_model: str | None = None
    image_extraction_enabled: bool = False
    max_image_size_mb: float = 5.0

    # Structure
    header_detection: bool = True
    header_hierarchy_enabled: bool = False  # Détection H1/H2/H3
    footer_removal: bool = True
    page_number_removal: bool = True

    # Qualité
    pdf_extraction_method: Literal["pypdf", "pdfplumber", "pdfminer", "unstructured"] = "pdfplumber"
    preserve_formatting: bool = True
    extract_hyperlinks: bool = False
    extract_footnotes: bool = False
```

**Implémentation**:

```python
# ragkit/ingestion/parsers/advanced_pdf_parser.py

from typing import Any
from pathlib import Path
import pdfplumber
from PIL import Image

class AdvancedPDFParser:
    """Parser PDF avancé avec support OCR, tables, images."""

    def __init__(self, config: DocumentParsingConfig):
        self.config = config
        self._ocr_engine = None
        self._vision_model = None

    async def parse(self, file_path: Path) -> ParsedDocument:
        """Parse un PDF avec toutes les fonctionnalités avancées."""

        with pdfplumber.open(file_path) as pdf:
            pages = []

            for page_num, page in enumerate(pdf.pages, start=1):
                page_data = await self._parse_page(page, page_num)
                pages.append(page_data)

        return ParsedDocument(
            content=self._merge_pages(pages),
            metadata={
                "total_pages": len(pages),
                "has_tables": any(p.get("tables") for p in pages),
                "has_images": any(p.get("images") for p in pages),
            },
            pages=pages,
        )

    async def _parse_page(self, page: Any, page_num: int) -> dict:
        """Parse une page individuelle."""

        # Extraction texte
        text = page.extract_text()

        # Si pas de texte et OCR activé
        if not text and self.config.ocr_enabled:
            text = await self._ocr_page(page)

        # Extraction tableaux
        tables = []
        if self.config.table_extraction_strategy != "none":
            tables = await self._extract_tables(page)

        # Extraction images
        images = []
        if self.config.image_extraction_enabled:
            images = await self._extract_images(page)

        # Captions d'images
        if self.config.image_captioning_enabled and images:
            for img in images:
                img["caption"] = await self._generate_caption(img["data"])

        # Nettoyage
        if self.config.footer_removal:
            text = self._remove_footer(text)
        if self.config.page_number_removal:
            text = self._remove_page_number(text, page_num)

        # Détection headers
        headers = []
        if self.config.header_detection:
            headers = self._detect_headers(text)

        return {
            "page_number": page_num,
            "text": text,
            "tables": tables,
            "images": images,
            "headers": headers,
            "metadata": {
                "width": page.width,
                "height": page.height,
            },
        }

    async def _extract_tables(self, page: Any) -> list[dict]:
        """Extrait les tableaux selon la stratégie configurée."""

        if self.config.table_extraction_strategy == "vision":
            # Utiliser un modèle vision pour détecter les tableaux
            return await self._extract_tables_vision(page)

        # Utiliser pdfplumber
        tables = page.find_tables()

        result = []
        for table in tables:
            if self.config.table_extraction_strategy == "markdown":
                result.append({
                    "type": "markdown",
                    "content": self._table_to_markdown(table.extract()),
                })
            elif self.config.table_extraction_strategy == "preserve":
                result.append({
                    "type": "structured",
                    "rows": table.extract(),
                    "bbox": table.bbox,
                })
            elif self.config.table_extraction_strategy == "separate":
                result.append({
                    "type": "separate_chunk",
                    "content": self._table_to_text(table.extract()),
                    "bbox": table.bbox,
                })

        return result

    async def _ocr_page(self, page: Any) -> str:
        """Effectue l'OCR sur une page."""

        if self._ocr_engine is None:
            self._ocr_engine = self._init_ocr_engine()

        # Convertir page en image
        image = page.to_image(resolution=self.config.ocr_dpi).original

        # Preprocessing si activé
        if self.config.ocr_preprocessing:
            image = self._preprocess_for_ocr(image)

        # OCR
        if self.config.ocr_engine == "tesseract":
            import pytesseract
            lang = "+".join(self.config.ocr_language)
            text = pytesseract.image_to_string(image, lang=lang)
        elif self.config.ocr_engine == "easyocr":
            import easyocr
            reader = easyocr.Reader(self.config.ocr_language)
            result = reader.readtext(image)
            text = "\n".join([item[1] for item in result])
        elif self.config.ocr_engine == "doctr":
            from doctr.models import ocr_predictor
            model = ocr_predictor(pretrained=True)
            result = model([image])
            text = result.render()

        return text
```

### 2.2 Text Preprocessing

**Paramètres à implémenter** (section 1.2):

```python
# ragkit/config/schema_v2.py

class TextPreprocessingConfig(BaseModel):
    """Configuration du preprocessing de texte."""

    # Normalisation basique
    lowercase: bool = False
    remove_punctuation: bool = False
    normalize_unicode: Literal["NFC", "NFD", "NFKC", "NFKD", "none"] = "NFC"
    remove_urls: bool = False
    remove_emails: bool = False
    remove_phone_numbers: bool = False

    # Détection langue
    language_detection: bool = False
    language_detector: Literal["langdetect", "fasttext", "langid"] = "langdetect"
    fallback_language: str = "en"

    # Déduplication
    deduplication_strategy: Literal["none", "exact", "fuzzy", "semantic"] = "none"
    deduplication_threshold: float = 0.95
    deduplication_scope: Literal["document", "chunk", "global"] = "chunk"

    # Nettoyage avancé
    remove_special_characters: bool = False
    normalize_whitespace: bool = True
    remove_extra_newlines: bool = True
    fix_encoding_errors: bool = True

    # Filtres personnalisés
    custom_regex_filters: list[str] = []
    custom_replacement_rules: dict[str, str] = {}
```

**Implémentation**:

```python
# ragkit/ingestion/preprocessing.py

import re
import unicodedata
from difflib import SequenceMatcher

class TextPreprocessor:
    """Preprocessing de texte avancé."""

    def __init__(self, config: TextPreprocessingConfig):
        self.config = config
        self._language_detector = None

    def process(self, text: str) -> str:
        """Applique tous les preprocessings configurés."""

        # Fix encoding
        if self.config.fix_encoding_errors:
            text = self._fix_encoding(text)

        # Unicode normalization
        if self.config.normalize_unicode != "none":
            text = unicodedata.normalize(self.config.normalize_unicode, text)

        # Nettoyage URLs
        if self.config.remove_urls:
            text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)

        # Nettoyage emails
        if self.config.remove_emails:
            text = re.sub(r'\S+@\S+', '', text)

        # Whitespace normalization
        if self.config.normalize_whitespace:
            text = re.sub(r'\s+', ' ', text)

        # Newlines
        if self.config.remove_extra_newlines:
            text = re.sub(r'\n{3,}', '\n\n', text)

        # Lowercase
        if self.config.lowercase:
            text = text.lower()

        # Punctuation
        if self.config.remove_punctuation:
            text = re.sub(r'[^\w\s]', '', text)

        # Custom filters
        for pattern in self.config.custom_regex_filters:
            text = re.sub(pattern, '', text)

        # Custom replacements
        for old, new in self.config.custom_replacement_rules.items():
            text = text.replace(old, new)

        return text.strip()

    async def detect_language(self, text: str) -> str:
        """Détecte la langue du texte."""

        if not self.config.language_detection:
            return self.config.fallback_language

        if self._language_detector is None:
            self._language_detector = self._init_language_detector()

        try:
            if self.config.language_detector == "langdetect":
                from langdetect import detect
                return detect(text)
            elif self.config.language_detector == "fasttext":
                import fasttext
                # Utiliser modèle lid.176.bin
                predictions = self._language_detector.predict(text.replace('\n', ' '))
                return predictions[0][0].replace('__label__', '')
            elif self.config.language_detector == "langid":
                import langid
                return langid.classify(text)[0]
        except Exception:
            return self.config.fallback_language

    def check_duplicate(self, text: str, existing_texts: list[str]) -> bool:
        """Vérifie si le texte est un doublon."""

        if self.config.deduplication_strategy == "none":
            return False

        if self.config.deduplication_strategy == "exact":
            return text in existing_texts

        elif self.config.deduplication_strategy == "fuzzy":
            for existing in existing_texts:
                similarity = SequenceMatcher(None, text, existing).ratio()
                if similarity >= self.config.deduplication_threshold:
                    return True
            return False

        elif self.config.deduplication_strategy == "semantic":
            # Nécessite embeddings - sera implémenté en Phase 4
            pass

        return False
```

### 2.3 Tests Unitaires Phase 2

```python
# tests/test_ingestion_advanced.py

import pytest
from pathlib import Path
from ragkit.ingestion.parsers.advanced_pdf_parser import AdvancedPDFParser
from ragkit.config.schema_v2 import DocumentParsingConfig

class TestAdvancedPDFParser:
    """Tests pour le parser PDF avancé."""

    @pytest.fixture
    def parser_config(self):
        return DocumentParsingConfig(
            ocr_enabled=True,
            ocr_language=["eng"],
            table_extraction_strategy="markdown",
            header_detection=True,
        )

    @pytest.mark.asyncio
    async def test_parse_pdf_with_tables(self, parser_config, tmp_path):
        """Test parsing PDF avec tableaux."""
        # Créer un PDF test avec tableaux
        test_pdf = tmp_path / "test_with_tables.pdf"
        # ... créer PDF test

        parser = AdvancedPDFParser(parser_config)
        result = await parser.parse(test_pdf)

        assert result.metadata["has_tables"] is True
        assert len(result.pages) > 0

        # Vérifier qu'au moins une table a été extraite
        has_table = any(
            page.get("tables") for page in result.pages
        )
        assert has_table

    @pytest.mark.asyncio
    async def test_ocr_on_scanned_pdf(self, tmp_path):
        """Test OCR sur PDF scanné."""
        config = DocumentParsingConfig(
            ocr_enabled=True,
            ocr_engine="tesseract",
            ocr_language=["eng"],
        )

        # Créer un PDF scanné (image)
        test_pdf = tmp_path / "scanned.pdf"
        # ... créer PDF scanné

        parser = AdvancedPDFParser(config)
        result = await parser.parse(test_pdf)

        # Vérifier que du texte a été extrait via OCR
        assert result.content
        assert len(result.content) > 100  # Texte significatif


class TestTextPreprocessing:
    """Tests pour le preprocessing."""

    def test_url_removal(self):
        """Test suppression URLs."""
        config = TextPreprocessingConfig(remove_urls=True)
        preprocessor = TextPreprocessor(config)

        text = "Check out https://example.com for more info"
        result = preprocessor.process(text)

        assert "https://example.com" not in result
        assert "Check out" in result

    def test_deduplication_exact(self):
        """Test déduplication exacte."""
        config = TextPreprocessingConfig(
            deduplication_strategy="exact"
        )
        preprocessor = TextPreprocessor(config)

        existing = ["This is a test document"]

        assert preprocessor.check_duplicate(
            "This is a test document", existing
        ) is True
        assert preprocessor.check_duplicate(
            "This is different", existing
        ) is False

    def test_deduplication_fuzzy(self):
        """Test déduplication fuzzy."""
        config = TextPreprocessingConfig(
            deduplication_strategy="fuzzy",
            deduplication_threshold=0.9,
        )
        preprocessor = TextPreprocessor(config)

        existing = ["This is a test document for deduplication"]

        # Très similaire (quelques caractères différents)
        assert preprocessor.check_duplicate(
            "This is a test document for deduplicaton", existing  # typo
        ) is True

        # Assez différent
        assert preprocessor.check_duplicate(
            "Completely different text here", existing
        ) is False
```

---

## Phase 3: Chunking Avancé

**Objectif**: Implémenter toutes les stratégies de chunking et paramètres associés

**État**: [ ] En cours | [ ] À tester | [ ] Testé | [ ] Terminé

### 3.1 Stratégies de Chunking

**Paramètres à implémenter** (section 2 du guide exhaustif):

```python
# ragkit/config/schema_v2.py

class ChunkingConfigV2(BaseModel):
    """Configuration complète du chunking."""

    # Stratégie
    strategy: Literal[
        "fixed_size",
        "sentence_based",
        "paragraph_based",
        "semantic",
        "markdown_header",
        "recursive",
        "parent_child",  # NOUVEAU
        "sliding_window",  # NOUVEAU
    ] = "fixed_size"

    # Tailles
    chunk_size: int = Field(512, ge=50, le=4000)
    chunk_overlap: int = Field(50, ge=0, le=1000)
    min_chunk_size: int = Field(50, ge=10)
    max_chunk_size: int = Field(2000, ge=100)

    # Séparateurs (pour recursive)
    separators: list[str] = ["\n\n", "\n", ". ", " ", ""]
    keep_separator: bool = True
    separator_regex: str | None = None

    # Parent-Child Chunking
    parent_chunk_size: int = 2000
    child_chunk_size: int = 400
    parent_child_overlap: int = 100

    # Sliding Window
    sentence_window_size: int = 3  # Phrases de contexte
    window_stride: int = 1

    # Semantic Chunking
    semantic_similarity_threshold: float = 0.85
    semantic_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    semantic_buffer_size: int = 1  # Phrases avant/après breakpoint

    # Markdown Header
    markdown_headers_to_split_on: list[tuple[str, str]] = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]

    # Metadata Enrichment
    add_metadata: bool = True
    add_chunk_index: bool = True
    add_document_title: bool = True
    add_section_title: bool = False
    add_page_number: bool = False
    add_paragraph_index: bool = False

    # Qualité
    strip_whitespace: bool = True
    merge_short_chunks: bool = True
    split_long_sentences: bool = False
```

**Implémentation du Parent-Child Chunking**:

```python
# ragkit/ingestion/chunkers/parent_child_chunker.py

from dataclasses import dataclass

@dataclass
class Chunk:
    content: str
    metadata: dict
    parent_id: str | None = None
    child_ids: list[str] = None

class ParentChildChunker:
    """Parent-Child chunking pour contexte élargi."""

    def __init__(self, config: ChunkingConfigV2):
        self.config = config
        self.base_chunker = FixedSizeChunker(
            chunk_size=config.child_chunk_size,
            chunk_overlap=config.parent_child_overlap,
        )
        self.parent_chunker = FixedSizeChunker(
            chunk_size=config.parent_chunk_size,
            chunk_overlap=config.parent_child_overlap,
        )

    async def chunk_async(self, document: ParsedDocument) -> list[Chunk]:
        """Crée des chunks parent-child."""

        # Créer les parents
        parent_chunks = await self.parent_chunker.chunk_async(document)

        all_chunks = []

        for parent_idx, parent in enumerate(parent_chunks):
            parent_id = f"parent_{parent_idx}"

            # Créer les enfants à partir du parent
            child_chunks = await self.base_chunker.chunk_async(
                ParsedDocument(content=parent.content, metadata=parent.metadata)
            )

            child_ids = []

            for child_idx, child in enumerate(child_chunks):
                child_id = f"{parent_id}_child_{child_idx}"
                child_ids.append(child_id)

                # Le child référence son parent
                child.metadata.update({
                    "chunk_id": child_id,
                    "parent_id": parent_id,
                    "parent_content": parent.content,  # Contexte élargi
                    "chunk_type": "child",
                })

                all_chunks.append(child)

            # Stocker aussi le parent (optionnel, pour retrieval)
            parent.metadata.update({
                "chunk_id": parent_id,
                "child_ids": child_ids,
                "chunk_type": "parent",
            })
            # On ne retourne que les enfants pour l'embedding
            # Le parent est stocké comme métadonnée

        return all_chunks
```

**Implémentation du Semantic Chunking**:

```python
# ragkit/ingestion/chunkers/semantic_chunker.py

import numpy as np
from sentence_transformers import SentenceTransformer

class SemanticChunker:
    """Chunking basé sur la similarité sémantique."""

    def __init__(self, config: ChunkingConfigV2):
        self.config = config
        self.model = SentenceTransformer(config.semantic_embedding_model)
        self.threshold = config.semantic_similarity_threshold

    async def chunk_async(self, document: ParsedDocument) -> list[Chunk]:
        """Découpe selon les breakpoints sémantiques."""

        # Découper en phrases
        sentences = self._split_into_sentences(document.content)

        if len(sentences) <= 1:
            return [Chunk(content=document.content, metadata={})]

        # Embedder toutes les phrases
        embeddings = self.model.encode(sentences)

        # Calculer similarités entre phrases adjacentes
        similarities = []
        for i in range(len(embeddings) - 1):
            sim = self._cosine_similarity(embeddings[i], embeddings[i + 1])
            similarities.append(sim)

        # Détecter les breakpoints (similarité < threshold)
        breakpoints = [0]
        for i, sim in enumerate(similarities):
            if sim < self.threshold:
                breakpoints.append(i + 1)
        breakpoints.append(len(sentences))

        # Créer les chunks
        chunks = []
        for i in range(len(breakpoints) - 1):
            start = breakpoints[i]
            end = breakpoints[i + 1]

            # Ajouter buffer si configuré
            buffer = self.config.semantic_buffer_size
            start_buffered = max(0, start - buffer)
            end_buffered = min(len(sentences), end + buffer)

            chunk_sentences = sentences[start_buffered:end_buffered]
            chunk_content = " ".join(chunk_sentences)

            chunks.append(Chunk(
                content=chunk_content,
                metadata={
                    "chunk_index": i,
                    "sentence_start": start,
                    "sentence_end": end,
                    "buffer_size": buffer,
                },
            ))

        # Merger les chunks trop courts
        if self.config.merge_short_chunks:
            chunks = self._merge_short_chunks(chunks)

        return chunks

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calcule la similarité cosinus."""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def _split_into_sentences(self, text: str) -> list[str]:
        """Découpe le texte en phrases."""
        import nltk
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')

        return nltk.sent_tokenize(text)

    def _merge_short_chunks(self, chunks: list[Chunk]) -> list[Chunk]:
        """Fusionne les chunks trop courts."""
        merged = []
        buffer = None

        for chunk in chunks:
            if len(chunk.content) < self.config.min_chunk_size:
                if buffer is None:
                    buffer = chunk
                else:
                    # Fusionner avec le buffer
                    buffer.content += " " + chunk.content
            else:
                if buffer is not None:
                    merged.append(buffer)
                    buffer = None
                merged.append(chunk)

        if buffer is not None:
            merged.append(buffer)

        return merged
```

### 3.2 Tests Unitaires Phase 3

```python
# tests/test_chunking_advanced.py

import pytest
from ragkit.ingestion.chunkers import (
    ParentChildChunker,
    SemanticChunker,
    SlidingWindowChunker,
)
from ragkit.config.schema_v2 import ChunkingConfigV2

class TestParentChildChunking:
    """Tests pour le parent-child chunking."""

    @pytest.fixture
    def config(self):
        return ChunkingConfigV2(
            strategy="parent_child",
            parent_chunk_size=1000,
            child_chunk_size=300,
            parent_child_overlap=50,
        )

    @pytest.mark.asyncio
    async def test_creates_parent_child_relationship(self, config):
        """Test création de la relation parent-child."""
        chunker = ParentChildChunker(config)

        # Document long (>1000 tokens)
        text = "This is a test. " * 200  # ~800 tokens
        document = ParsedDocument(content=text, metadata={})

        chunks = await chunker.chunk_async(document)

        # Vérifier structure
        assert len(chunks) > 0

        # Tous les chunks sont des enfants
        for chunk in chunks:
            assert chunk.metadata["chunk_type"] == "child"
            assert "parent_id" in chunk.metadata
            assert "parent_content" in chunk.metadata

            # Le parent doit être plus grand
            assert len(chunk.metadata["parent_content"]) > len(chunk.content)

    @pytest.mark.asyncio
    async def test_parent_provides_context(self, config):
        """Test que le parent fournit du contexte."""
        chunker = ParentChildChunker(config)

        # Document avec sections distinctes
        text = (
            "Introduction to AI. "
            "Artificial Intelligence is a field of computer science. "
            * 50  # Section 1
            + "Machine Learning basics. "
            "ML is a subset of AI. "
            * 50  # Section 2
        )

        document = ParsedDocument(content=text, metadata={})
        chunks = await chunker.chunk_async(document)

        # Vérifier que chaque child a accès au contexte parent
        for chunk in chunks:
            parent_content = chunk.metadata["parent_content"]
            # Le parent contient le chunk ET du contexte supplémentaire
            assert chunk.content in parent_content
            assert len(parent_content) > len(chunk.content)


class TestSemanticChunking:
    """Tests pour le semantic chunking."""

    @pytest.fixture
    def config(self):
        return ChunkingConfigV2(
            strategy="semantic",
            semantic_similarity_threshold=0.75,
            semantic_buffer_size=1,
            merge_short_chunks=True,
            min_chunk_size=50,
        )

    @pytest.mark.asyncio
    async def test_splits_on_topic_change(self, config):
        """Test découpage sur changement de sujet."""
        chunker = SemanticChunker(config)

        # Texte avec 2 sujets distincts
        text = (
            "Python is a programming language. "
            "It was created by Guido van Rossum. "
            "Python is widely used for web development. "  # Sujet 1: Python
            "Elephants are large mammals. "
            "They live in Africa and Asia. "
            "Elephants have long trunks. "  # Sujet 2: Éléphants (complètement différent)
        )

        document = ParsedDocument(content=text, metadata={})
        chunks = await chunker.chunk_async(document)

        # Devrait créer au moins 2 chunks (sujets différents)
        assert len(chunks) >= 2

        # Premier chunk devrait parler de Python
        assert "Python" in chunks[0].content or "programming" in chunks[0].content

        # Dernier chunk devrait parler d'éléphants
        assert "Elephant" in chunks[-1].content or "trunk" in chunks[-1].content

    @pytest.mark.asyncio
    async def test_merges_short_chunks(self, config):
        """Test fusion des chunks courts."""
        chunker = SemanticChunker(config)

        # Texte avec phrases très courtes
        text = "Hi. Bye. Hello. Goodbye."

        document = ParsedDocument(content=text, metadata={})
        chunks = await chunker.chunk_async(document)

        # Tous les chunks doivent respecter min_chunk_size
        for chunk in chunks:
            assert len(chunk.content) >= config.min_chunk_size
```

---

## Phase 4: Embedding & Vector DB

**Objectif**: Configuration complète des embeddings et de la base vectorielle

**État**: [ ] En cours | [ ] À tester | [ ] Testé | [ ] Terminé

### 4.1 Configuration Embedding Avancée

**Paramètres** (section 3 du guide exhaustif):

```python
# ragkit/config/schema_v2.py

class EmbeddingConfigV2(BaseModel):
    """Configuration complète des embeddings."""

    # Modèle
    model: str = "text-embedding-3-small"
    provider: Literal[
        "openai",
        "cohere",
        "huggingface",
        "sentence_transformers",
        "ollama",
        "voyage",
        "onnx_local",
    ] = "openai"

    # Dimensions
    dimensions: int | None = None
    dimensionality_reduction: Literal["none", "pca", "umap"] = "none"
    reduction_target_dims: int | None = None

    # Normalisation
    normalize_embeddings: bool = True
    embedding_dtype: Literal["float32", "float16", "int8"] = "float32"

    # Batching
    batch_size: int = 32
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit_rpm: int | None = None
    rate_limit_tpm: int | None = None

    # Gestion des tokens
    max_tokens_per_chunk: int = 8192
    truncation_strategy: Literal["start", "end", "middle", "split"] = "end"
    pooling_strategy: Literal["mean", "max", "cls", "last"] = "mean"

    # API
    api_key: str | None = None
    api_key_env: str | None = None
    api_base_url: str | None = None
    timeout: int = 60

    # Cache
    cache_embeddings: bool = True
    cache_size_mb: int = 512

    # Modèles séparés query/document
    use_separate_query_model: bool = False
    query_model: str | None = None
    query_instruction_prefix: str | None = None
    document_instruction_prefix: str | None = None
```

**Implémentation avancée**:

```python
# ragkit/embedding/advanced_embedder.py

import numpy as np
from typing import Protocol
import asyncio
from functools import lru_cache

class RateLimiter:
    """Rate limiter pour respecter les quotas API."""

    def __init__(self, rpm: int | None, tpm: int | None):
        self.rpm = rpm
        self.tpm = tpm
        self.request_times = []
        self.token_count = 0
        self.last_reset = asyncio.get_event_loop().time()

    async def acquire(self, tokens: int):
        """Attend si nécessaire pour respecter les limites."""
        now = asyncio.get_event_loop().time()

        # Reset toutes les 60 secondes
        if now - self.last_reset >= 60:
            self.request_times = []
            self.token_count = 0
            self.last_reset = now

        # Vérifier RPM
        if self.rpm is not None:
            self.request_times = [
                t for t in self.request_times if now - t < 60
            ]
            if len(self.request_times) >= self.rpm:
                wait_time = 60 - (now - self.request_times[0])
                if wait_time > 0:
                    await asyncio.sleep(wait_time)

        # Vérifier TPM
        if self.tpm is not None and self.token_count + tokens > self.tpm:
            await asyncio.sleep(60 - (now - self.last_reset))
            self.token_count = 0
            self.last_reset = asyncio.get_event_loop().time()

        self.request_times.append(now)
        self.token_count += tokens


class AdvancedEmbedder:
    """Embedder avec toutes les fonctionnalités avancées."""

    def __init__(self, config: EmbeddingConfigV2):
        self.config = config
        self.rate_limiter = RateLimiter(
            config.rate_limit_rpm,
            config.rate_limit_tpm,
        )
        self.cache = {} if config.cache_embeddings else None
        self._reduction_model = None

    async def embed_batch(self, texts: list[str]) -> np.ndarray:
        """Embedde un batch de textes avec gestion avancée."""

        # Preprocessing
        processed_texts = [self._preprocess_text(t) for t in texts]

        # Truncation si nécessaire
        processed_texts = [
            self._truncate_text(t) for t in processed_texts
        ]

        # Cache lookup
        embeddings = []
        texts_to_embed = []
        cache_keys = []

        for text in processed_texts:
            cache_key = self._get_cache_key(text)
            if self.cache is not None and cache_key in self.cache:
                embeddings.append(self.cache[cache_key])
                cache_keys.append(None)
            else:
                embeddings.append(None)
                texts_to_embed.append(text)
                cache_keys.append(cache_key)

        # Embedder les textes non cachés
        if texts_to_embed:
            # Rate limiting
            total_tokens = sum(len(t.split()) for t in texts_to_embed)
            await self.rate_limiter.acquire(total_tokens)

            # Appel API avec retry
            new_embeddings = await self._embed_with_retry(texts_to_embed)

            # Normalisation
            if self.config.normalize_embeddings:
                new_embeddings = self._normalize(new_embeddings)

            # Réduction dimensionnalité
            if self.config.dimensionality_reduction != "none":
                new_embeddings = await self._reduce_dimensions(new_embeddings)

            # Conversion dtype
            if self.config.embedding_dtype == "float16":
                new_embeddings = new_embeddings.astype(np.float16)
            elif self.config.embedding_dtype == "int8":
                new_embeddings = self._quantize_int8(new_embeddings)

            # Mise en cache
            if self.cache is not None:
                for i, cache_key in enumerate(cache_keys):
                    if cache_key is not None:
                        self.cache[cache_key] = new_embeddings[i]

            # Combiner avec cache
            new_idx = 0
            for i in range(len(embeddings)):
                if embeddings[i] is None:
                    embeddings[i] = new_embeddings[new_idx]
                    new_idx += 1

        return np.array(embeddings)

    async def _embed_with_retry(self, texts: list[str]) -> np.ndarray:
        """Embedde avec retry automatique."""
        for attempt in range(self.config.max_retries):
            try:
                return await self._call_embedding_api(texts)
            except Exception as e:
                if attempt == self.config.max_retries - 1:
                    raise
                await asyncio.sleep(self.config.retry_delay * (2 ** attempt))

    async def _call_embedding_api(self, texts: list[str]) -> np.ndarray:
        """Appelle l'API d'embedding."""
        if self.config.provider == "openai":
            import openai
            client = openai.AsyncOpenAI(api_key=self.config.api_key)

            # Ajouter préfixes si configurés
            if self.config.document_instruction_prefix:
                texts = [
                    f"{self.config.document_instruction_prefix}{t}"
                    for t in texts
                ]

            response = await client.embeddings.create(
                model=self.config.model,
                input=texts,
                dimensions=self.config.dimensions,
            )

            embeddings = [item.embedding for item in response.data]
            return np.array(embeddings)

        elif self.config.provider == "sentence_transformers":
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(self.config.model)

            embeddings = model.encode(
                texts,
                batch_size=self.config.batch_size,
                show_progress_bar=False,
            )

            return embeddings

        # ... autres providers

    def _truncate_text(self, text: str) -> str:
        """Tronque le texte selon la stratégie."""
        tokens = text.split()  # Simplification

        if len(tokens) <= self.config.max_tokens_per_chunk:
            return text

        if self.config.truncation_strategy == "start":
            return " ".join(tokens[:self.config.max_tokens_per_chunk])
        elif self.config.truncation_strategy == "end":
            return " ".join(tokens[-self.config.max_tokens_per_chunk:])
        elif self.config.truncation_strategy == "middle":
            half = self.config.max_tokens_per_chunk // 2
            return " ".join(tokens[:half] + tokens[-half:])
        elif self.config.truncation_strategy == "split":
            # Sera géré en amont par chunking
            return " ".join(tokens[:self.config.max_tokens_per_chunk])

    async def _reduce_dimensions(self, embeddings: np.ndarray) -> np.ndarray:
        """Réduit la dimensionnalité."""
        if self._reduction_model is None:
            if self.config.dimensionality_reduction == "pca":
                from sklearn.decomposition import PCA
                self._reduction_model = PCA(
                    n_components=self.config.reduction_target_dims
                )
            elif self.config.dimensionality_reduction == "umap":
                from umap import UMAP
                self._reduction_model = UMAP(
                    n_components=self.config.reduction_target_dims
                )

        return self._reduction_model.fit_transform(embeddings)

    def _normalize(self, embeddings: np.ndarray) -> np.ndarray:
        """L2 normalisation."""
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        return embeddings / norms

    def _quantize_int8(self, embeddings: np.ndarray) -> np.ndarray:
        """Quantification int8."""
        # Normaliser dans [-127, 127]
        min_val = embeddings.min()
        max_val = embeddings.max()
        scale = 127.0 / max(abs(min_val), abs(max_val))
        return (embeddings * scale).astype(np.int8)

    def _get_cache_key(self, text: str) -> str:
        """Génère une clé de cache."""
        import hashlib
        return hashlib.md5(text.encode()).hexdigest()
```

### 4.2 Configuration Vector DB Complète

**Paramètres** (section 4 du guide exhaustif):

```python
# ragkit/config/schema_v2.py

class VectorDBConfigV2(BaseModel):
    """Configuration complète de la base vectorielle."""

    # Provider
    provider: Literal[
        "chromadb",
        "qdrant",
        "pinecone",
        "weaviate",
        "milvus",
        "faiss",
    ] = "chromadb"

    # Métrique de distance
    distance_metric: Literal[
        "cosine",
        "euclidean",
        "dot_product",
        "manhattan",
    ] = "cosine"

    # Type d'index
    index_type: Literal[
        "HNSW",
        "IVF",
        "FLAT",
        "LSH",
        "IVF_FLAT",
        "IVF_PQ",
    ] = "HNSW"

    # Paramètres HNSW
    hnsw_m: int = 16  # Connexions par nœud
    hnsw_ef_construction: int = 200
    hnsw_ef_search: int = 50

    # Paramètres IVF
    ivf_nlist: int | None = None  # Calculé auto si None
    ivf_nprobe: int = 10

    # Quantization
    quantization_type: Literal["none", "scalar", "product", "binary"] = "none"
    pq_m: int = 8  # Sous-vecteurs pour Product Quantization
    pq_nbits: int = 8

    # Sharding & Réplication
    num_shards: int = 1
    num_replicas: int = 1
    replication_factor: int = 1

    # Filtrage
    metadata_index_fields: list[str] = []
    filter_strategy: Literal["pre_filter", "post_filter"] = "pre_filter"

    # Performance
    batch_size: int = 100
    max_concurrent_operations: int = 10
    connection_pool_size: int = 10

    # Stockage
    storage_path: str | None = None
    in_memory: bool = False
    persist_on_disk: bool = True
```

Due to message length limits, I'll save the complete plan to the file. This is a comprehensive plan with 150+ RAG parameters across 12 phases.
