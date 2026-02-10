"""Tokenizers for lexical retrieval."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod

from ragkit.config.schema_v2 import RetrievalConfigV2


class BaseTokenizer(ABC):
    """Abstract base class for tokenizers."""

    @abstractmethod
    def tokenize(self, text: str) -> list[str]:
        """Tokenize text into list of tokens."""
        pass


class StandardTokenizer(BaseTokenizer):
    """Standard tokenizer: split on whitespace and punctuation."""

    def __init__(
        self,
        lowercase: bool = True,
        remove_stopwords: bool = False,
        stopwords_language: str = "english",
        custom_stopwords: list[str] | None = None,
        stemming: bool = False,
    ):
        """Initialize standard tokenizer.

        Args:
            lowercase: Convert to lowercase
            remove_stopwords: Remove stopwords
            stopwords_language: Language for stopwords
            custom_stopwords: Additional custom stopwords
            stemming: Apply stemming
        """
        self.lowercase = lowercase
        self.remove_stopwords = remove_stopwords
        self.stemming = stemming

        # Load stopwords if needed
        self.stopwords = set()
        if remove_stopwords:
            self.stopwords = self._load_stopwords(stopwords_language)
            if custom_stopwords:
                self.stopwords.update(custom_stopwords)

        # Initialize stemmer if needed
        self.stemmer = None
        if stemming:
            try:
                from nltk.stem import PorterStemmer

                self.stemmer = PorterStemmer()
            except ImportError:
                print("Warning: NLTK not available, stemming disabled")

    def tokenize(self, text: str) -> list[str]:
        """Tokenize text.

        Args:
            text: Input text

        Returns:
            List of tokens
        """
        # Lowercase
        if self.lowercase:
            text = text.lower()

        # Split on whitespace and punctuation
        tokens = re.findall(r"\b\w+\b", text)

        # Remove stopwords
        if self.remove_stopwords:
            tokens = [t for t in tokens if t not in self.stopwords]

        # Apply stemming
        if self.stemmer:
            tokens = [self.stemmer.stem(t) for t in tokens]

        return tokens

    def _load_stopwords(self, language: str) -> set[str]:
        """Load stopwords for given language."""
        try:
            from nltk.corpus import stopwords

            return set(stopwords.words(language))
        except (ImportError, LookupError):
            # Fallback: basic English stopwords
            return {
                "a",
                "an",
                "and",
                "are",
                "as",
                "at",
                "be",
                "by",
                "for",
                "from",
                "has",
                "he",
                "in",
                "is",
                "it",
                "its",
                "of",
                "on",
                "that",
                "the",
                "to",
                "was",
                "will",
                "with",
            }


class WhitespaceTokenizer(BaseTokenizer):
    """Whitespace tokenizer: split only on whitespace."""

    def __init__(self, lowercase: bool = True):
        self.lowercase = lowercase

    def tokenize(self, text: str) -> list[str]:
        """Tokenize on whitespace only."""
        if self.lowercase:
            text = text.lower()
        return text.split()


class NGramTokenizer(BaseTokenizer):
    """N-gram tokenizer: generates n-grams."""

    def __init__(
        self,
        ngram_range: tuple[int, int] = (1, 2),
        lowercase: bool = True,
    ):
        """Initialize n-gram tokenizer.

        Args:
            ngram_range: Range of n-gram sizes (min, max)
            lowercase: Convert to lowercase
        """
        self.ngram_range = ngram_range
        self.lowercase = lowercase

    def tokenize(self, text: str) -> list[str]:
        """Generate n-grams."""
        if self.lowercase:
            text = text.lower()

        # Split into words
        words = re.findall(r"\b\w+\b", text)

        # Generate n-grams
        ngrams = []
        for n in range(self.ngram_range[0], self.ngram_range[1] + 1):
            for i in range(len(words) - n + 1):
                ngram = " ".join(words[i : i + n])
                ngrams.append(ngram)

        return ngrams


def create_tokenizer(config: RetrievalConfigV2) -> BaseTokenizer:
    """Create tokenizer from config.

    Args:
        config: Retrieval configuration

    Returns:
        Tokenizer instance
    """
    if config.tokenizer_type == "standard":
        return StandardTokenizer(
            lowercase=config.lowercase_tokens,
            remove_stopwords=config.remove_stopwords,
            stopwords_language=config.stopwords_language,
            custom_stopwords=config.custom_stopwords,
            stemming=config.stemming_enabled,
        )
    elif config.tokenizer_type == "whitespace":
        return WhitespaceTokenizer(lowercase=config.lowercase_tokens)
    elif config.tokenizer_type == "ngram":
        return NGramTokenizer(
            ngram_range=config.ngram_range,
            lowercase=config.lowercase_tokens,
        )
    else:
        raise ValueError(f"Unknown tokenizer type: {config.tokenizer_type}")
