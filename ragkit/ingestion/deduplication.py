"""Document-level deduplication for the ingestion pipeline."""

from __future__ import annotations

import hashlib
import logging
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class DocumentDeduplicator:
    """Track ingested documents and reject duplicates.

    Supports two strategies:

    * **exact** – SHA-256 hash of the normalised content.
    * **fuzzy** – SequenceMatcher ratio against previously registered texts
      (only practical for small corpora; for large-scale fuzzy dedup consider
      SimHash / MinHash which can be added later).
    """

    def __init__(
        self,
        strategy: str = "exact",
        threshold: float = 0.95,
    ) -> None:
        self.strategy = strategy
        self.threshold = threshold
        self._hashes: set[str] = set()
        self._texts: list[str] = []  # only populated for fuzzy strategy

    def is_duplicate(self, content: str) -> bool:
        """Return *True* if *content* has already been registered."""
        if self.strategy == "none":
            return False

        if self.strategy == "exact":
            h = self._exact_hash(content)
            return h in self._hashes

        if self.strategy == "fuzzy":
            for existing in self._texts:
                ratio = SequenceMatcher(None, content, existing).ratio()
                if ratio >= self.threshold:
                    return True
            return False

        logger.warning("Unknown deduplication strategy: %s", self.strategy)
        return False

    def register(self, content: str) -> None:
        """Add *content* to the known-document registry."""
        if self.strategy == "exact":
            self._hashes.add(self._exact_hash(content))
        elif self.strategy == "fuzzy":
            self._texts.append(content)

    @staticmethod
    def _exact_hash(content: str) -> str:
        """SHA-256 of whitespace-normalised content."""
        normalised = " ".join(content.split())
        return hashlib.sha256(normalised.encode("utf-8")).hexdigest()

    def reset(self) -> None:
        """Clear the deduplication registry."""
        self._hashes.clear()
        self._texts.clear()
