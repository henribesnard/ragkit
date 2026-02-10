"""Text preprocessing utilities for ingestion."""

from __future__ import annotations

import logging
import re
import unicodedata
from collections.abc import Callable
from difflib import SequenceMatcher
from typing import Any

from ragkit.config.schema_v2 import TextPreprocessingConfig

logger = logging.getLogger(__name__)


class TextPreprocessor:
    """Preprocess and normalize text before chunking."""

    def __init__(
        self,
        config: TextPreprocessingConfig,
        embedder: Callable[[list[str]], Any] | None = None,
    ) -> None:
        self.config = config
        self._embedder = embedder
        self._language_detector = None

    def process(self, text: str) -> str:
        """Apply preprocessing steps to input text."""
        if not isinstance(text, str):
            text = str(text)

        if self.config.fix_encoding_errors:
            text = self._fix_encoding_errors(text)

        if self.config.normalize_unicode and self.config.normalize_unicode != "none":
            text = unicodedata.normalize(self.config.normalize_unicode, text)

        if self.config.remove_urls:
            text = re.sub(r"https?://\S+|www\.\S+", "", text)

        if self.config.remove_emails:
            text = re.sub(r"\b[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}\b", "", text)

        if self.config.remove_phone_numbers:
            text = re.sub(r"\b\+?\d[\d\s\-\(\)]{7,}\d\b", "", text)

        if self.config.custom_regex_filters:
            for pattern in self.config.custom_regex_filters:
                text = re.sub(pattern, "", text)

        if self.config.custom_replacement_rules:
            for pattern, replacement in self.config.custom_replacement_rules.items():
                text = text.replace(pattern, replacement)

        if self.config.remove_punctuation:
            text = re.sub(r"[^\w\s]", "", text)

        if self.config.remove_special_characters:
            text = "".join(ch for ch in text if ch.isalnum() or ch.isspace())

        if self.config.remove_control_characters:
            text = "".join(
                char for char in text if unicodedata.category(char)[0] != "C"
            )

        if self.config.remove_extra_newlines:
            text = re.sub(r"\n{3,}", "\n\n", text)

        if self.config.normalize_whitespace:
            text = re.sub(r"[\t\r\f\v]+", " ", text)
            text = re.sub(r" {2,}", " ", text)

        if self.config.lowercase:
            text = text.lower()

        if self.config.remove_stopwords:
            text = self._remove_stopwords(text)

        return text.strip()

    def check_duplicate(self, text: str, existing_texts: list[str]) -> bool:
        """Check whether text is a duplicate of existing content."""
        strategy = self.config.deduplication_strategy
        threshold = self.config.deduplication_threshold

        if strategy == "none":
            return False

        if strategy == "exact":
            return text in existing_texts

        if strategy == "fuzzy":
            for existing in existing_texts:
                ratio = SequenceMatcher(None, text, existing).ratio()
                if ratio >= threshold:
                    return True
            return False

        if strategy == "semantic":
            if self._embedder is None:
                logger.warning("Semantic deduplication requested but no embedder provided")
                return False
            return self._semantic_duplicate(text, existing_texts, threshold)

        return False

    async def detect_language(self, text: str) -> str:
        """Detect the language of a text snippet."""
        if not self.config.language_detection:
            return self.config.fallback_language

        if len(text) < self.config.min_text_length_for_detection:
            return self.config.fallback_language

        if self.config.language_detector == "langdetect":
            try:
                from langdetect import detect
            except Exception as exc:  # noqa: BLE001
                logger.warning("langdetect unavailable: %s", exc)
                return self.config.fallback_language
            return detect(text)

        if self.config.language_detector == "langid":
            try:
                import langid
            except Exception as exc:  # noqa: BLE001
                logger.warning("langid unavailable: %s", exc)
                return self.config.fallback_language
            return langid.classify(text)[0]

        if self.config.language_detector == "fasttext":
            try:
                import fasttext
            except Exception as exc:  # noqa: BLE001
                logger.warning("fasttext unavailable: %s", exc)
                return self.config.fallback_language

            if self._language_detector is None:
                model_path = "lid.176.bin"
                self._language_detector = fasttext.load_model(model_path)

            prediction = self._language_detector.predict(text, k=1)
            label = prediction[0][0]
            return label.replace("__label__", "")

        return self.config.fallback_language

    def _semantic_duplicate(
        self,
        text: str,
        existing_texts: list[str],
        threshold: float,
    ) -> bool:
        """Use embeddings to detect semantic duplicates."""
        try:
            import numpy as np
        except Exception as exc:  # noqa: BLE001
            logger.warning("Numpy required for semantic deduplication: %s", exc)
            return False

        embeddings = self._embedder([text] + existing_texts)
        if embeddings is None or len(embeddings) != len(existing_texts) + 1:
            return False

        target = np.array(embeddings[0])
        others = np.array(embeddings[1:])
        if target.ndim == 0 or others.size == 0:
            return False

        if target.ndim == 1:
            target_norm = np.linalg.norm(target) or 1.0
            others_norm = np.linalg.norm(others, axis=1) + 1e-9
            similarities = (others @ target) / (others_norm * target_norm)
        else:
            return False

        return bool((similarities >= threshold).any())

    def _fix_encoding_errors(self, text: str) -> str:
        """Attempt to fix common encoding issues."""
        try:
            return text.encode("utf-8", errors="ignore").decode("utf-8")
        except Exception:  # noqa: BLE001
            return text

    def _remove_stopwords(self, text: str) -> str:
        """Remove stopwords using NLTK when available."""
        try:
            import nltk
            from nltk.corpus import stopwords
        except Exception as exc:  # noqa: BLE001
            logger.warning("Stopwords removal failed: %s", exc)
            return text

        try:
            nltk.data.find("corpora/stopwords")
        except LookupError:
            nltk.download("stopwords", quiet=True)

        try:
            stop_words = set(stopwords.words(self.config.stopwords_language))
        except Exception:  # noqa: BLE001
            stop_words = set()

        stop_words.update(self.config.custom_stopwords)
        words = text.split()
        filtered = [word for word in words if word.lower() not in stop_words]
        return " ".join(filtered)
