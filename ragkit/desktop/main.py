"""RAGKIT Desktop backend entry point.

This module starts the FastAPI server that handles requests from the
Tauri desktop application.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import signal
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ragkit.desktop.api import router as api_router
from ragkit.desktop.state import AppState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global state
app_state: AppState | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifecycle."""
    global app_state

    logger.info("Starting RAGKIT Desktop backend...")

    # Initialize app state
    app_state = AppState()
    await app_state.initialize()
    app.state.app_state = app_state

    logger.info("RAGKIT Desktop backend ready")

    yield

    # Cleanup
    logger.info("Shutting down RAGKIT Desktop backend...")
    if app_state:
        await app_state.shutdown()


def create_app() -> FastAPI:
    """Create the FastAPI application."""
    app = FastAPI(
        title="RAGKIT Desktop API",
        description="Backend API for RAGKIT Desktop application",
        version="1.5.0",
        lifespan=lifespan,
    )

    # CORS middleware (allow Tauri webview)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(api_router)

    # Health check endpoint
    @app.get("/health")
    async def health_check() -> dict[str, Any]:
        return {
            "ok": True,
            "version": "1.5.0",
        }

    # Shutdown endpoint (called by Tauri on app close)
    @app.post("/shutdown")
    async def shutdown() -> dict[str, bool]:
        logger.info("Shutdown requested")
        # Schedule shutdown after response is sent
        asyncio.get_event_loop().call_later(0.5, lambda: sys.exit(0))
        return {"ok": True}

    return app


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="RAGKIT Desktop Backend")
    parser.add_argument(
        "--port",
        type=int,
        default=8100,
        help="Port to run the server on",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind to",
    )
    args = parser.parse_args()

    # Create app
    app = create_app()

    # Setup signal handlers for graceful shutdown
    def handle_signal(signum: int, frame: Any) -> None:
        logger.info(f"Received signal {signum}, shutting down...")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    # Run server
    logger.info(f"Starting server on {args.host}:{args.port}")
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
