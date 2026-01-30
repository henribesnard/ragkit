"""Lexical retrieval using BM25."""

from __future__ import annotations

import re

from rank_bm25 import BM25Okapi, BM25Plus  # type: ignore

from ragkit.config.schema import LexicalRetrievalConfig
from ragkit.models import Chunk, RetrievalResult


class TextPreprocessor:
    def __init__(self, config) -> None:
        self.config = config
        self.stopwords = _get_stopwords(config.stopwords_lang)

    def tokenize(self, text: str) -> list[str]:
        tokens = _tokenize(text)
        if self.config.lowercase:
            tokens = [token.lower() for token in tokens]
        if self.config.remove_stopwords:
            tokens = [token for token in tokens if token not in self.stopwords]
        if self.config.stemming:
            tokens = [_stem(token) for token in tokens]
        return [token for token in tokens if token]


class LexicalRetriever:
    def __init__(self, config: LexicalRetrievalConfig) -> None:
        self.config = config
        self.preprocessor = TextPreprocessor(config.preprocessing)
        self.chunks: list[Chunk] = []
        self.bm25 = None

    def index(self, chunks: list[Chunk]) -> None:
        self.chunks = chunks
        tokenized = [self.preprocessor.tokenize(chunk.content) for chunk in chunks]
        if self.config.algorithm == "bm25+":
            self.bm25 = BM25Plus(tokenized, k1=self.config.params.k1, b=self.config.params.b)
        else:
            self.bm25 = BM25Okapi(tokenized, k1=self.config.params.k1, b=self.config.params.b)

    def retrieve(self, query: str) -> list[RetrievalResult]:
        if self.bm25 is None:
            return []
        tokenized_query = self.preprocessor.tokenize(query)
        if not tokenized_query:
            return []
        scores = list(self.bm25.get_scores(tokenized_query))
        ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)
        top = ranked[: self.config.top_k]

        results: list[RetrievalResult] = []
        for index, score in top:
            chunk = self.chunks[index]
            results.append(
                RetrievalResult(
                    chunk=chunk,
                    score=float(score),
                    retrieval_type="lexical",
                )
            )
        return results


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text)


def _get_stopwords(language: str) -> set[str]:
    if language == "french":
        return _FRENCH_STOPWORDS
    if language == "english":
        return _ENGLISH_STOPWORDS
    return _ENGLISH_STOPWORDS | _FRENCH_STOPWORDS


def _stem(token: str) -> str:
    # Simple suffix stripping for English/French without extra dependencies.
    for suffix in ("ing", "ed", "ly", "es", "s", "ment", "tion", "ions", "ement"):
        if token.endswith(suffix) and len(token) > len(suffix) + 2:
            return token[: -len(suffix)]
    return token


_ENGLISH_STOPWORDS = {
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
    "were",
    "will",
    "with",
}

_FRENCH_STOPWORDS = {
    "alors",
    "au",
    "aucuns",
    "aussi",
    "autre",
    "avant",
    "avec",
    "avoir",
    "bon",
    "car",
    "ce",
    "cela",
    "ces",
    "ceux",
    "chaque",
    "comme",
    "comment",
    "dans",
    "des",
    "du",
    "elle",
    "elles",
    "en",
    "encore",
    "est",
    "et",
    "eu",
    "fait",
    "faites",
    "fois",
    "font",
    "hors",
    "ici",
    "il",
    "ils",
    "je",
    "juste",
    "la",
    "le",
    "les",
    "leur",
    "ma",
    "maintenant",
    "mais",
    "mes",
    "mine",
    "moins",
    "mon",
    "mot",
    "meme",
    "ni",
    "notre",
    "nous",
    "ou",
    "par",
    "parce",
    "pas",
    "peut",
    "peu",
    "plupart",
    "pour",
    "pourquoi",
    "quand",
    "que",
    "quel",
    "quelle",
    "quelles",
    "quels",
    "qui",
    "sa",
    "sans",
    "ses",
    "seulement",
    "si",
    "son",
    "sont",
    "sous",
    "sur",
    "ta",
    "tandis",
    "te",
    "tellement",
    "tels",
    "tes",
    "ton",
    "tous",
    "tout",
    "trop",
    "tres",
    "tu",
    "voient",
    "vont",
    "votre",
    "vous",
    "vu",
}
