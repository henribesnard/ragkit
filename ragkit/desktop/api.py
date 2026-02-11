"""REST API routes for RAGKIT Desktop.

This module defines the API endpoints that the Tauri frontend uses
to interact with the backend.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Literal, cast

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ragkit.config.defaults import default_ingestion_config
from ragkit.config.schema import ChunkingConfig, FixedChunkingConfig
from ragkit.desktop.logging_utils import LOG_BUFFER
from ragkit.desktop.wizard_api import router as wizard_router
from ragkit.ingestion.chunkers import create_chunker
from ragkit.ingestion.parsers import create_parser
from ragkit.ingestion.sources.base import RawDocument

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")
router.include_router(wizard_router)


# ============================================================================
# Request/Response Models
# ============================================================================


class CreateKnowledgeBaseRequest(BaseModel):
    name: str
    description: str | None = None
    embedding_model: str | None = None


class AddDocumentsRequest(BaseModel):
    paths: list[str]


class AddFolderRequest(BaseModel):
    folder_path: str
    recursive: bool = True
    file_types: list[str] = ["pdf", "txt", "md", "docx", "doc"]


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
    embedding_chunk_strategy: str = "fixed"
    embedding_chunk_size: int = 512
    embedding_chunk_overlap: int = 50
    retrieval_architecture: str = "semantic"
    retrieval_top_k: int = 10
    retrieval_semantic_weight: float = 1.0
    retrieval_lexical_weight: float = 0.0
    retrieval_rerank_weight: float = 0.0
    retrieval_rerank_enabled: bool = False
    retrieval_rerank_provider: str = "none"
    retrieval_max_chunks: int = 4
    llm_provider: str
    llm_model: str
    llm_temperature: float = 0.7
    llm_max_tokens: int = 1000
    llm_top_p: float = 0.95
    llm_system_prompt: str = ""
    theme: str


class SetApiKeyRequest(BaseModel):
    provider: str
    api_key: str


class TestApiKeyRequest(BaseModel):
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
    chunk_strategy: str = "fixed",
    chunk_size: int = 512,
    chunk_overlap: int = 50,
) -> int:
    ingestion_defaults = default_ingestion_config()
    chunking_config = ChunkingConfig(
        strategy=cast(Literal["fixed", "semantic"], chunk_strategy),
        fixed=FixedChunkingConfig(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        ),
    )
    parser = create_parser(ingestion_defaults.parsing)
    chunker = create_chunker(chunking_config, embedder=embedder)

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
    for chunk, embedding in zip(chunks, embeddings, strict=True):
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
    settings = state.get_settings()

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
                chunk_strategy=settings.get("embedding_chunk_strategy", "fixed"),
                chunk_size=settings.get("embedding_chunk_size", 512),
                chunk_overlap=settings.get("embedding_chunk_overlap", 50),
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


@router.post("/knowledge-bases/{kb_id}/folders")
async def add_folder(request: Request, kb_id: str, body: AddFolderRequest) -> dict[str, Any]:
    """Add all documents from a folder to a knowledge base."""
    state = get_state(request)

    # Verify KB exists
    kb = await state.kb_manager.get(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    folder_path = Path(body.folder_path)
    if not folder_path.exists() or not folder_path.is_dir():
        raise HTTPException(status_code=400, detail="Invalid folder path")

    embedder = state.get_embedder(kb.embedding_model, kb.embedding_dimensions)
    vector_store = state.kb_manager.get_vector_store(kb_id)
    settings = state.get_settings()

    file_types = [t.lower().lstrip(".") for t in body.file_types if t]
    file_types = list(dict.fromkeys(file_types)) if file_types else []

    files_to_add: list[Path] = []
    glob_pattern = "**/*" if body.recursive else "*"
    if file_types:
        for file_type in file_types:
            pattern = f"{glob_pattern}.{file_type}"
            files_to_add.extend(folder_path.glob(pattern))
    else:
        files_to_add = [p for p in folder_path.glob(glob_pattern) if p.is_file()]

    added: list[str] = []
    failed: list[dict[str, str]] = []
    for file_path in files_to_add:
        doc = None
        try:
            doc = await state.kb_manager.add_document(kb_id, str(file_path))
            added.append(doc.id)
            chunk_count = await _ingest_document(
                path=file_path,
                document_id=doc.id,
                embedder=embedder,
                vector_store=vector_store,
                chunk_strategy=settings.get("embedding_chunk_strategy", "fixed"),
                chunk_size=settings.get("embedding_chunk_size", 512),
                chunk_overlap=settings.get("embedding_chunk_overlap", 50),
            )
            await state.kb_manager.update_document_status(
                doc.id,
                status="indexed",
                chunk_count=chunk_count,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Failed to ingest document {file_path}: {e}")
            failed.append({"path": str(file_path), "error": str(e)})
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

    return {
        "added": added,
        "failed": failed,
        "total_processed": len(files_to_add),
    }


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

    if settings.embedding_chunk_size < 50 or settings.embedding_chunk_size > 2000:
        raise HTTPException(
            status_code=400,
            detail="Chunk size must be between 50 and 2000",
        )
    if settings.embedding_chunk_overlap >= settings.embedding_chunk_size:
        raise HTTPException(
            status_code=400,
            detail="Chunk overlap must be less than chunk size",
        )
    if settings.retrieval_top_k < 1 or settings.retrieval_top_k > 50:
        raise HTTPException(
            status_code=400,
            detail="Top K must be between 1 and 50",
        )
    if settings.retrieval_max_chunks < 1 or settings.retrieval_max_chunks > 50:
        raise HTTPException(
            status_code=400,
            detail="Max chunks must be between 1 and 50",
        )
    for weight_value, name in (
        (settings.retrieval_semantic_weight, "Semantic weight"),
        (settings.retrieval_lexical_weight, "Lexical weight"),
        (settings.retrieval_rerank_weight, "Rerank weight"),
    ):
        if weight_value < 0 or weight_value > 1:
            raise HTTPException(
                status_code=400,
                detail=f"{name} must be between 0 and 1",
            )

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


@router.post("/keys/test")
async def test_api_key(request: Request, body: TestApiKeyRequest) -> dict[str, Any]:
    """Test an API key by making a minimal call."""
    try:
        import litellm
    except ImportError:
        return {"ok": False, "error": "litellm not installed"}

    # Map providers to lightweight models for testing
    test_models = {
        "openai": "gpt-3.5-turbo",
        "anthropic": "claude-3-haiku-20240307",
        "deepseek": "deepseek/deepseek-chat",
        "groq": "groq/llama3-8b-8192",
        "mistral": "mistral/mistral-tiny",
        "gemini": "gemini/gemini-pro",
        "cohere": "command-r",
    }

    model = test_models.get(body.provider)
    if not model:
        # Fallback: try using the provider name as prefix
        if body.provider in ["ollama"]:
             # Ollama testing needs a running instance, skip api key test
             return {"ok": True, "message": "Local provider, skipped key test"}
        return {"ok": False, "error": f"Unsupported provider for testing: {body.provider}"}

    try:
        # Make a minimal generation request
        # We use max_tokens=1 to minimize cost/latency
        await litellm.acompletion(
            model=model,
            messages=[{"role": "user", "content": "Hi"}],
            api_key=body.api_key,
            max_tokens=1,
        )
        return {"ok": True}
    except Exception as exc:
        logger.warning(f"API key test failed for {body.provider}: {exc}")
        return {"ok": False, "error": str(exc)}


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
async def get_recommended_models(request: Request) -> dict[str, dict[str, Any]]:
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


@router.get("/logs")
async def get_logs(limit: int = 100) -> list[dict[str, Any]]:
    """Get recent logs."""
    buffer = list(LOG_BUFFER)
    # Return last N logs
    return buffer[-limit:]


@router.delete("/logs")
async def clear_logs() -> dict[str, bool]:
    """Clear logs."""
    LOG_BUFFER.clear()
    return {"ok": True}
