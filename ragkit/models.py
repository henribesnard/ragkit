"""Shared data models used across modules."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Document(BaseModel):
    id: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    embedding: list[float] | None = None


class Chunk(BaseModel):
    id: str
    document_id: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    embedding: list[float] | None = None


class RetrievalResult(BaseModel):
    chunk: Chunk
    score: float
    retrieval_type: str


class QueryAnalysis(BaseModel):
    intent: str
    needs_retrieval: bool
    rewritten_query: str | None = None
    reasoning: str | None = None


class GeneratedResponse(BaseModel):
    content: str
    sources: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RAGResponse(BaseModel):
    query: str
    analysis: QueryAnalysis
    context: list[RetrievalResult] | None = None
    response: GeneratedResponse
