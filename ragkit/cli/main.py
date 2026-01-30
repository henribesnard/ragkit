"""CLI entrypoint for RAGKIT."""

from __future__ import annotations

import asyncio
from pathlib import Path
import shutil

import typer

from ragkit.config import ConfigLoader
from ragkit.embedding import create_embedder
from ragkit.ingestion import IngestionPipeline
from ragkit.retrieval import RetrievalEngine
from ragkit.vectorstore import create_vector_store
from ragkit.llm import LLMRouter
from ragkit.agents import AgentOrchestrator

app = typer.Typer(name="ragkit", help="RAGKIT - Configuration-First RAG Framework")


@app.command()
def init(
    name: str = typer.Argument(..., help="Project name"),
    template: str = typer.Option("minimal", help="Template to use"),
) -> None:
    """Initialize a new RAGKIT project."""
    dest = Path(name)
    if dest.exists():
        raise typer.BadParameter(f"Destination already exists: {dest}")
    dest.mkdir(parents=True)

    template_path = Path(__file__).resolve().parent.parent.parent / "templates" / f"{template}.yaml"
    if not template_path.exists():
        raise typer.BadParameter(f"Unknown template: {template}")

    shutil.copy(template_path, dest / "ragkit.yaml")
    (dest / "data" / "documents").mkdir(parents=True, exist_ok=True)
    typer.echo(f"Created project at {dest}")


@app.command()
def validate(
    config: Path = typer.Option("ragkit.yaml", "--config", "-c", help="Config file path"),
) -> None:
    """Validate configuration file."""
    loader = ConfigLoader()
    loader.load_with_env(config)
    typer.echo("Configuration OK")


@app.command()
def ingest(
    config: Path = typer.Option("ragkit.yaml", "--config", "-c", help="Config file path"),
    incremental: bool = typer.Option(False, help="Only ingest modified files"),
) -> None:
    """Ingest documents into the vector store."""
    loader = ConfigLoader()
    cfg = loader.load_with_env(config)

    embedder = create_embedder(cfg.embedding.document_model)
    vector_store = create_vector_store(cfg.vector_store)
    pipeline = IngestionPipeline(cfg.ingestion, embedder=embedder, vector_store=vector_store)

    stats = asyncio.run(pipeline.run(incremental=incremental))
    typer.echo(f"Ingestion complete: {stats}")


@app.command()
def query(
    question: str = typer.Argument(..., help="Question to ask"),
    config: Path = typer.Option("ragkit.yaml", "--config", "-c", help="Config file path"),
) -> None:
    """Query the RAG system from command line."""
    loader = ConfigLoader()
    cfg = loader.load_with_env(config)

    embedder = create_embedder(cfg.embedding.query_model)
    vector_store = create_vector_store(cfg.vector_store)
    retrieval = RetrievalEngine(cfg.retrieval, vector_store, embedder)
    llm_router = LLMRouter(cfg.llm)
    orchestrator = AgentOrchestrator(cfg.agents, retrieval, llm_router)

    result = asyncio.run(orchestrator.process(question))
    typer.echo(result.response.content)


@app.command()
def serve(
    config: Path = typer.Option("ragkit.yaml", "--config", "-c", help="Config file path"),
    api_only: bool = typer.Option(False, help="Serve API only"),
    chatbot_only: bool = typer.Option(False, help="Serve chatbot only"),
) -> None:
    """Start the RAGKIT server."""
    if api_only and chatbot_only:
        raise typer.BadParameter("Choose either --api-only or --chatbot-only")

    loader = ConfigLoader()
    cfg = loader.load_with_env(config)

    embedder = create_embedder(cfg.embedding.query_model)
    vector_store = create_vector_store(cfg.vector_store)
    retrieval = RetrievalEngine(cfg.retrieval, vector_store, embedder)
    llm_router = LLMRouter(cfg.llm)
    orchestrator = AgentOrchestrator(cfg.agents, retrieval, llm_router)

    if not chatbot_only:
        from ragkit.api.app import create_app

        app_instance = create_app(cfg, orchestrator)
        import uvicorn

        if api_only:
            uvicorn.run(app_instance, host=cfg.api.server.host, port=cfg.api.server.port)
        else:
            import threading

            thread = threading.Thread(
                target=uvicorn.run,
                kwargs={\"app\": app_instance, \"host\": cfg.api.server.host, \"port\": cfg.api.server.port},
                daemon=True,
            )
            thread.start()

    if not api_only:
        from ragkit.chatbot.gradio_ui import create_chatbot

        ui = create_chatbot(cfg.chatbot, orchestrator)
        ui.launch(
            server_name=cfg.chatbot.server.host,
            server_port=cfg.chatbot.server.port,
            share=cfg.chatbot.server.share,
        )
