"""REST API routes for RAGKIT Desktop.

This module defines the API endpoints that the Tauri frontend uses
to interact with the backend.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ragkit.config.defaults import default_ingestion_config
from ragkit.ingestion.chunkers import create_chunker
from ragkit.ingestion.parsers import create_parser
from ragkit.ingestion.sources.base import RawDocument

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


# ============================================================================
# Request/Response Models
# ============================================================================


class CreateKnowledgeBaseRequest(BaseModel):
    name: str
    description: str | None = None
    embedding_model: str | None = None


class AddDocumentsRequest(BaseModel):
    paths: list[str]


class CreateConversationRequest(BaseModel):
    kb_id: str | None = None
    title: str | None = None


class QueryRequest(BaseModel):
    kb_id: str
    conversation_id: str
    question: str


class SettingsModel(BaseModel):
    embedding_provider: str
    embedding_model: str
    llm_provider: str
    llm_model: str
    theme: str


class SetApiKeyRequest(BaseModel):
    provider: str
    api_key: str


# ============================================================================
# Helper Functions
# ============================================================================


def get_state(request: Request) -> Any:
    """Get app state from request."""
    return request.app.state.app_state


def _detect_file_type(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".")
    if suffix in {"md", "markdown"}:
        return "md"
    if suffix:
        return suffix
    return "unknown"


def _read_content(path: Path, file_type: str) -> bytes | str:
    if file_type in {"md", "txt"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    return path.read_bytes()


async def _ingest_document(
    *,
    path: Path,
    document_id: str,
    embedder: Any,
    vector_store: Any,
) -> int:
    ingestion_defaults = default_ingestion_config()
    parser = create_parser(ingestion_defaults.parsing)
    chunker = create_chunker(ingestion_defaults.chunking, embedder=embedder)

    file_type = _detect_file_type(path)
    stat = path.stat()
    metadata = {
        "document_id": document_id,
        "source_path": str(path),
        "file_name": path.name,
        "file_type": file_type,
        "size": stat.st_size,
        "modified_time": stat.st_mtime,
    }
    raw_doc = RawDocument(
        content=_read_content(path, file_type),
        source_path=str(path),
        file_type=file_type,
        metadata=metadata,
    )

    parsed = await parser.parse(raw_doc)
    chunks = await chunker.chunk_async(parsed)
    if not chunks:
        return 0

    embeddings = await embedder.embed([chunk.content for chunk in chunks])
    if len(embeddings) != len(chunks):
        raise RuntimeError(
            f"Embedding count mismatch: {len(embeddings)} embeddings for {len(chunks)} chunks"
        )
    for chunk, embedding in zip(chunks, embeddings):
        chunk.embedding = embedding

    await vector_store.add(chunks)
    return len(chunks)


def _source_filename(metadata: dict[str, Any], fallback: str = "unknown") -> str:
    source = metadata.get("file_name") or metadata.get("source") or metadata.get("source_path")
    if source:
        return Path(str(source)).name
    return fallback


# ============================================================================
# Knowledge Base Routes
# ============================================================================


@router.get("/knowledge-bases")
async def list_knowledge_bases(request: Request) -> list[dict[str, Any]]:
    """List all knowledge bases."""
    state = get_state(request)
    kbs = await state.kb_manager.list()
    return [
        {
            "id": kb.id,
            "name": kb.name,
            "description": kb.description,
            "embedding_model": kb.embedding_model,
            "embedding_dimensions": kb.embedding_dimensions,
            "document_count": kb.document_count,
            "chunk_count": kb.chunk_count,
            "created_at": kb.created_at,
            "updated_at": kb.updated_at,
        }
        for kb in kbs
    ]


@router.post("/knowledge-bases")
async def create_knowledge_base(
    request: Request, body: CreateKnowledgeBaseRequest
) -> dict[str, Any]:
    """Create a new knowledge base."""
    state = get_state(request)

    try:
        kb = await state.kb_manager.create(
            name=body.name,
            description=body.description,
            embedding_model=body.embedding_model or state.get_settings()["embedding_model"],
        )
        return {
            "id": kb.id,
            "name": kb.name,
            "description": kb.description,
            "embedding_model": kb.embedding_model,
            "embedding_dimensions": kb.embedding_dimensions,
            "document_count": kb.document_count,
            "chunk_count": kb.chunk_count,
            "created_at": kb.created_at,
            "updated_at": kb.updated_at,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete("/knowledge-bases/{kb_id}")
async def delete_knowledge_base(request: Request, kb_id: str) -> bool:
    """Delete a knowledge base."""
    state = get_state(request)
    deleted = await state.kb_manager.delete(kb_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return True


@router.post("/knowledge-bases/{kb_id}/documents")
async def add_documents(request: Request, kb_id: str, body: AddDocumentsRequest) -> dict[str, Any]:
    """Add documents to a knowledge base."""
    state = get_state(request)

    # Verify KB exists
    kb = await state.kb_manager.get(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    embedder = state.get_embedder(kb.embedding_model, kb.embedding_dimensions)
    vector_store = state.kb_manager.get_vector_store(kb_id)

    # Add each document
    added = []
    for path in body.paths:
        doc = None
        try:
            doc = await state.kb_manager.add_document(kb_id, path)
            added.append(doc.id)
            chunk_count = await _ingest_document(
                path=Path(path),
                document_id=doc.id,
                embedder=embedder,
                vector_store=vector_store,
            )
            await state.kb_manager.update_document_status(
                doc.id,
                status="indexed",
                chunk_count=chunk_count,
            )
        except (FileNotFoundError, ValueError, RuntimeError) as e:
            logger.warning(f"Failed to ingest document {path}: {e}")
            if doc is not None:
                await state.kb_manager.update_document_status(
                    doc.id,
                    status="error",
                    error_message=str(e),
                )

    await state.kb_manager.update_stats(kb_id)
    try:
        orchestrator = await state.get_orchestrator(kb_id)
        await orchestrator.retrieval.refresh_lexical_index()
    except Exception:  # noqa: BLE001
        pass

    return {"added": added}


# ============================================================================
# Conversation Routes
# ============================================================================


@router.get("/conversations")
async def list_conversations(request: Request, kb_id: str | None = None) -> list[dict[str, Any]]:
    """List conversations."""
    state = get_state(request)
    convs = await state.conversation_manager.list(kb_id=kb_id)
    return [
        {
            "id": c.id,
            "kb_id": c.kb_id,
            "title": c.title,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
        }
        for c in convs
    ]


@router.post("/conversations")
async def create_conversation(request: Request, body: CreateConversationRequest) -> dict[str, Any]:
    """Create a new conversation."""
    state = get_state(request)
    conv = await state.conversation_manager.create(
        kb_id=body.kb_id,
        title=body.title,
    )
    return {
        "id": conv.id,
        "kb_id": conv.kb_id,
        "title": conv.title,
        "created_at": conv.created_at,
        "updated_at": conv.updated_at,
    }


@router.delete("/conversations/{conv_id}")
async def delete_conversation(request: Request, conv_id: str) -> bool:
    """Delete a conversation."""
    state = get_state(request)
    deleted = await state.conversation_manager.delete(conv_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return True


@router.get("/conversations/{conv_id}/messages")
async def get_messages(request: Request, conv_id: str) -> list[dict[str, Any]]:
    """Get messages in a conversation."""
    state = get_state(request)
    messages = await state.conversation_manager.get_messages(conv_id)
    return [
        {
            "id": m.id,
            "conversation_id": m.conversation_id,
            "role": m.role,
            "content": m.content,
            "sources": m.sources,
            "latency_ms": m.latency_ms,
            "created_at": m.created_at,
        }
        for m in messages
    ]


# ============================================================================
# Query Route
# ============================================================================


@router.post("/query")
async def query(request: Request, body: QueryRequest) -> dict[str, Any]:
    """Query a knowledge base."""
    state = get_state(request)

    # Verify KB exists
    kb = await state.kb_manager.get(body.kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    # Load conversation history
    history_messages = await state.conversation_manager.get_messages(body.conversation_id)
    history = [
        {"role": msg.role, "content": msg.content}
        for msg in history_messages
        if msg.role in {"user", "assistant"}
    ]

    # Add user message to conversation
    await state.conversation_manager.add_message(
        conversation_id=body.conversation_id,
        role="user",
        content=body.question,
    )

    orchestrator = await state.get_orchestrator(body.kb_id)
    start = time.perf_counter()
    result = await orchestrator.process(body.question, history)
    latency_ms = int((time.perf_counter() - start) * 1000)

    sources_payload = []
    for item in result.context or []:
        sources_payload.append(
            {
                "filename": _source_filename(item.chunk.metadata, fallback=kb.name),
                "chunk": item.chunk.content,
                "score": item.score,
            }
        )

    # Add assistant message
    await state.conversation_manager.add_message(
        conversation_id=body.conversation_id,
        role="assistant",
        content=result.response.content,
        sources=sources_payload,
        latency_ms=latency_ms,
    )

    return {
        "answer": result.response.content,
        "sources": sources_payload,
        "latency_ms": latency_ms,
    }


# ============================================================================
# Settings Routes
# ============================================================================


@router.get("/settings")
async def get_settings(request: Request) -> dict[str, Any]:
    """Get application settings."""
    state = get_state(request)
    return state.get_settings()


@router.put("/settings")
async def update_settings(request: Request, settings: SettingsModel) -> dict[str, Any]:
    """Update application settings."""
    state = get_state(request)
    updated = state.update_settings(settings.model_dump())
    return updated


# ============================================================================
# API Key Routes
# ============================================================================


@router.post("/keys")
async def set_api_key(request: Request, body: SetApiKeyRequest) -> dict[str, bool]:
    """Store an API key."""
    state = get_state(request)
    state.key_store.store(body.provider, body.api_key)
    return {"ok": True}


@router.get("/keys/{provider}")
async def has_api_key(request: Request, provider: str) -> dict[str, bool]:
    """Check if an API key exists."""
    state = get_state(request)
    exists = state.key_store.has_key(provider)
    return {"exists": exists}


@router.delete("/keys/{provider}")
async def delete_api_key(request: Request, provider: str) -> bool:
    """Delete an API key."""
    state = get_state(request)
    deleted = state.key_store.delete(provider)
    return deleted


# ============================================================================
# Ollama Routes
# ============================================================================


@router.get("/ollama/status")
async def get_ollama_status(request: Request) -> dict[str, Any]:
    """Get Ollama service status."""
    state = get_state(request)
    status = await state.ollama_manager.get_status()
    return {
        "installed": status.installed,
        "running": status.running,
        "version": status.version,
        "error": status.error,
    }


@router.get("/ollama/models")
async def list_ollama_models(request: Request) -> list[dict[str, Any]]:
    """List installed Ollama models."""
    state = get_state(request)
    models = await state.ollama_manager.list_models()
    return [
        {
            "name": m.name,
            "size": m.size,
            "size_formatted": state.ollama_manager.format_size(m.size),
            "digest": m.digest,
            "modified_at": m.modified_at,
        }
        for m in models
    ]


@router.get("/ollama/recommended")
async def get_recommended_models(request: Request) -> list[dict[str, Any]]:
    """Get list of recommended models."""
    state = get_state(request)
    return state.ollama_manager.get_recommended_models()


@router.get("/ollama/embedding-models")
async def get_ollama_embedding_models(request: Request) -> list[dict[str, Any]]:
    """Get list of Ollama embedding models."""
    state = get_state(request)
    return state.ollama_manager.get_embedding_models()


class PullModelRequest(BaseModel):
    model_name: str


@router.post("/ollama/pull")
async def pull_ollama_model(request: Request, body: PullModelRequest) -> dict[str, Any]:
    """Pull (download) an Ollama model."""
    state = get_state(request)

    # Check if Ollama is running
    if not await state.ollama_manager.is_running():
        raise HTTPException(
            status_code=503,
            detail="Ollama is not running. Please start Ollama first.",
        )

    # Start pull in background (we can't stream progress through REST easily)
    success = await state.ollama_manager.pull_model(body.model_name)

    if not success:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to pull model {body.model_name}",
        )

    return {"ok": True, "model": body.model_name}


class DeleteModelRequest(BaseModel):
    model_name: str


@router.delete("/ollama/models")
async def delete_ollama_model(request: Request, body: DeleteModelRequest) -> dict[str, bool]:
    """Delete an Ollama model."""
    state = get_state(request)
    success = await state.ollama_manager.delete_model(body.model_name)

    if not success:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete model {body.model_name}",
        )

    return {"ok": True}


@router.post("/ollama/start")
async def start_ollama_service(request: Request) -> dict[str, bool]:
    """Attempt to start the Ollama service."""
    state = get_state(request)

    if not state.ollama_manager.is_installed():
        raise HTTPException(
            status_code=400,
            detail="Ollama is not installed",
        )

    success = await state.ollama_manager.start_service()

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to start Ollama service",
        )

    return {"ok": True}


@router.get("/ollama/install-instructions")
async def get_install_instructions() -> dict[str, Any]:
    """Get Ollama installation instructions."""
    import sys

    from ragkit.llm.providers.ollama_manager import OllamaManager

    instructions = OllamaManager.get_install_instructions()
    platform = sys.platform

    return {
        "platform": platform,
        "instructions": instructions.get(platform, instructions.get("linux", "")),
        "all_platforms": instructions,
    }
