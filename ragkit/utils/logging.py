"""Logging utilities based on structlog."""

from __future__ import annotations

import logging
from logging.handlers import TimedRotatingFileHandler

import structlog

from ragkit.config.schema import ObservabilityConfig


def _build_handlers(config: ObservabilityConfig) -> list[logging.Handler]:
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    file_cfg = config.logging.file
    if file_cfg.enabled and file_cfg.path:
        if file_cfg.rotation == "daily":
            handler = TimedRotatingFileHandler(
                file_cfg.path,
                when="D",
                backupCount=file_cfg.retention_days or 7,
                encoding="utf-8",
            )
        else:
            handler = logging.FileHandler(file_cfg.path, encoding="utf-8")
        handlers.append(handler)
    return handlers


def setup_logging(config: ObservabilityConfig) -> structlog.BoundLogger:
    """Configure structlog according to config."""
    level = getattr(logging, config.logging.level, logging.INFO)
    handlers = _build_handlers(config)

    logging.basicConfig(level=level, handlers=handlers, format="%(message)s")

    processors: list[structlog.types.Processor] = [
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if config.logging.format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger()
