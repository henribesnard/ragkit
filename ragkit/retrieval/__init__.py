"""Retrieval module exports."""

# Legacy imports (v1)
from ragkit.retrieval.engine import RetrievalEngine
from ragkit.retrieval.fusion import ScoreFusion
from ragkit.retrieval.lexical import LexicalRetriever as LexicalRetrieverV1
from ragkit.retrieval.lexical import TextPreprocessor
from ragkit.retrieval.rerank import BaseReranker, CohereReranker, NoOpReranker, create_reranker
from ragkit.retrieval.semantic import SemanticRetriever as SemanticRetrieverV1

# New imports (v2 - Phase 5)
from ragkit.retrieval.base_retriever import BaseRetriever, SearchResult
from ragkit.retrieval.hybrid_retriever import HybridRetriever
from ragkit.retrieval.lexical_retriever import LexicalRetriever
from ragkit.retrieval.mmr import maximal_marginal_relevance
from ragkit.retrieval.query_expander import QueryExpander
from ragkit.retrieval.semantic_retriever import SemanticRetriever

__all__ = [
    # Legacy v1
    "RetrievalEngine",
    "SemanticRetrieverV1",
    "LexicalRetrieverV1",
    "TextPreprocessor",
    "ScoreFusion",
    "BaseReranker",
    "CohereReranker",
    "NoOpReranker",
    "create_reranker",
    # New v2 (Phase 5)
    "BaseRetriever",
    "SearchResult",
    "SemanticRetriever",
    "LexicalRetriever",
    "HybridRetriever",
    "QueryExpander",
    "maximal_marginal_relevance",
]
