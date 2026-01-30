"""CLI entrypoint for RAGKIT."""

from __future__ import annotations

import asyncio
import shutil
import subprocess
from pathlib import Path

import typer

from ragkit.agents import AgentOrchestrator
from ragkit.config import ConfigLoader
from ragkit.embedding import create_embedder
from ragkit.ingestion import IngestionPipeline
from ragkit.llm import LLMRouter
from ragkit.retrieval import RetrievalEngine
from ragkit.vectorstore import create_vector_store

app = typer.Typer(name="ragkit", help="RAGKIT - Configuration-First RAG Framework")
ui_app = typer.Typer(help="UI commands")
app.add_typer(ui_app, name="ui")


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

    embedder_query = create_embedder(cfg.embedding.query_model)
    vector_store = create_vector_store(cfg.vector_store)
    retrieval = RetrievalEngine(cfg.retrieval, vector_store, embedder_query)
    llm_router = LLMRouter(cfg.llm)
    orchestrator = AgentOrchestrator(
        cfg.agents,
        retrieval,
        llm_router,
        metrics_enabled=cfg.observability.metrics.enabled,
    )

    result = asyncio.run(orchestrator.process(question))
    typer.echo(result.response.content)


@app.command()
def serve(
    config: Path = typer.Option("ragkit.yaml", "--config", "-c", help="Config file path"),
    api_only: bool = typer.Option(False, help="Serve API only"),
    chatbot_only: bool = typer.Option(False, help="Serve chatbot only"),
    with_ui: bool = typer.Option(False, help="Serve the Web UI if built"),
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
    orchestrator = AgentOrchestrator(
        cfg.agents,
        retrieval,
        llm_router,
        metrics_enabled=cfg.observability.metrics.enabled,
    )

    if not chatbot_only:
        from ragkit.api.app import create_app

        if with_ui:
            ui_dist = Path(__file__).resolve().parent.parent / "ui" / "dist"
            if not ui_dist.exists():
                typer.echo("UI build not found. Run `ragkit ui build` first.")

        app_instance = create_app(
            cfg,
            orchestrator,
            config_path=config,
            vector_store=vector_store,
            embedder=embedder,
            llm_router=llm_router,
        )
        import uvicorn

        if api_only:
            uvicorn.run(app_instance, host=cfg.api.server.host, port=cfg.api.server.port)
        else:
            import threading

            thread = threading.Thread(
                target=uvicorn.run,
                kwargs={
                    "app": app_instance,
                    "host": cfg.api.server.host,
                    "port": cfg.api.server.port,
                },
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
            theme=cfg.chatbot.ui.theme,
            title=cfg.chatbot.ui.title,
        )


@ui_app.command("build")
def build_ui() -> None:
    """Build the RAGKIT Web UI and copy assets into the Python package."""
    root = Path(__file__).resolve().parent.parent.parent
    ui_path = root / "ragkit-ui"
    if not ui_path.exists():
        raise typer.BadParameter("ragkit-ui directory not found")

    subprocess.run(["npm", "install"], cwd=ui_path, check=True)
    subprocess.run(["npm", "run", "build"], cwd=ui_path, check=True)

    target = root / "ragkit" / "ui" / "dist"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(ui_path / "dist", target)
    typer.echo(f"UI build copied to {target}")


@ui_app.command("dev")
def dev_ui() -> None:
    """Run the UI dev server (Vite)."""
    root = Path(__file__).resolve().parent.parent.parent
    ui_path = root / "ragkit-ui"
    if not ui_path.exists():
        raise typer.BadParameter("ragkit-ui directory not found")

    subprocess.run(["npm", "install"], cwd=ui_path, check=True)
    subprocess.run(["npm", "run", "dev"], cwd=ui_path, check=True)
