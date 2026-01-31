"""CLI entrypoint for RAGKIT."""

from __future__ import annotations

import asyncio
import shutil
import subprocess
from pathlib import Path
from typing import Any

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


def _display_host(host: str) -> str:
    if host in {"0.0.0.0", "::"}:
        return "localhost"
    return host


def _ensure_ui_assets() -> bool:
    ui_dist = Path(__file__).resolve().parent.parent / "ui" / "dist"
    if ui_dist.exists():
        return True

    ui_src = Path(__file__).resolve().parent.parent.parent / "ragkit-ui"
    if ui_src.exists():
        typer.echo("Building Web UI assets...")
        try:
            build_ui()
        except subprocess.CalledProcessError as exc:
            typer.echo(f"Web UI build failed: {exc}")
            return False
        return ui_dist.exists()

    return False


@app.command()
def init(
    name: str = typer.Argument(..., help="Project name"),
    template: str = typer.Option("setup", help="Template to use (setup, minimal, hybrid, full)"),
) -> None:
    """Initialize a new RAGKIT project."""
    dest = Path(name)
    if dest.exists():
        raise typer.BadParameter(f"Destination already exists: {dest}")
    dest.mkdir(parents=True)

    template_root = Path(__file__).resolve().parent.parent / "templates"
    template_path = template_root / f"{template}.yaml"
    if not template_path.exists():
        fallback_root = Path(__file__).resolve().parent.parent.parent / "templates"
        template_path = fallback_root / f"{template}.yaml"
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
    assert cfg.embedding is not None
    assert cfg.ingestion is not None

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
    assert cfg.embedding is not None
    assert cfg.retrieval is not None
    assert cfg.llm is not None
    assert cfg.agents is not None

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
    with_ui: bool = typer.Option(True, "--with-ui/--no-ui", help="Serve the Web UI (build if needed)"),
    port: int | None = typer.Option(None, "--port", help="Override the API port"),
) -> None:
    """Start the RAGKIT server."""
    if api_only and chatbot_only:
        raise typer.BadParameter("Choose either --api-only or --chatbot-only")

    loader = ConfigLoader()
    cfg = loader.load_with_env(config)
    setup_mode = not cfg.is_configured

    orchestrator = None
    vector_store = None
    embedder = None
    llm_router = None

    if not setup_mode:
        assert cfg.embedding is not None
        assert cfg.retrieval is not None
        assert cfg.llm is not None
        assert cfg.agents is not None
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
    else:
        typer.echo("Starting in setup mode - configure via the Web UI.")

    api_host = cfg.api.server.host
    api_port = port or cfg.api.server.port
    ui_ready = False
    if with_ui and not chatbot_only:
        ui_ready = _ensure_ui_assets()
        if not ui_ready:
            typer.echo("Web UI assets not found. Run `ragkit ui build` from source to enable the UI.")

    if not chatbot_only:
        from ragkit.api.app import create_app

        app_instance = create_app(
            cfg,
            orchestrator,
            config_path=config,
            vector_store=vector_store,
            embedder=embedder,
            llm_router=llm_router,
            setup_mode=setup_mode,
            mount_ui=with_ui,
        )
        import uvicorn

        if api_only:
            if with_ui and ui_ready:
                typer.echo(f"Web UI: http://{_display_host(api_host)}:{api_port}/")
            if cfg.api.docs.enabled:
                typer.echo(f"API docs: http://{_display_host(api_host)}:{api_port}/api/docs")
            uvicorn.run(app_instance, host=api_host, port=api_port)
        else:
            import threading

            thread = threading.Thread(
                target=uvicorn.run,
                kwargs={
                    "app": app_instance,
                    "host": api_host,
                    "port": api_port,
                },
                daemon=True,
            )
            thread.start()
            if with_ui and ui_ready:
                typer.echo(f"Web UI: http://{_display_host(api_host)}:{api_port}/")
            if cfg.api.docs.enabled:
                typer.echo(f"API docs: http://{_display_host(api_host)}:{api_port}/api/docs")

    if not api_only and not setup_mode:
        from ragkit.chatbot.gradio_ui import create_chatbot

        assert orchestrator is not None
        ui = create_chatbot(cfg.chatbot, orchestrator)
        launch_kwargs: dict[str, Any] = {
            "server_name": cfg.chatbot.server.host,
            "server_port": cfg.chatbot.server.port,
            "share": cfg.chatbot.server.share,
            "theme": cfg.chatbot.ui.theme,
            "title": cfg.chatbot.ui.title,
        }
        ui.launch(**launch_kwargs)
    elif setup_mode and not api_only:
        typer.echo("Chatbot UI disabled in setup mode. Use the Web UI to configure.")


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
