"""Source loader factory."""

from __future__ import annotations

from ragkit.config.schema import LocalSourceConfig, SourceConfig
from ragkit.ingestion.sources.base import BaseSourceLoader
from ragkit.ingestion.sources.local import LocalSourceLoader


def create_source_loader(config: SourceConfig) -> BaseSourceLoader:
    if config.type == "local":
        return LocalSourceLoader(LocalSourceConfig(**config.model_dump()))
    raise ValueError(f"Unknown source type: {config.type}")


__all__ = ["BaseSourceLoader", "LocalSourceLoader", "create_source_loader"]
