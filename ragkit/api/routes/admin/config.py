"""Admin configuration endpoints."""

from __future__ import annotations

import asyncio
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel

from ragkit.config.defaults import (
    default_agents_config,
    default_embedding_config,
    default_ingestion_config,
    default_llm_config,
    default_retrieval_config,
)
from ragkit.config.schema import RAGKitConfig
from ragkit.config.validators import validate_config as validate_custom

router = APIRouter(prefix="/config")


def _mask_secrets(data: dict) -> dict:
    """Recursively mask api_key values in a config dict."""
    if not isinstance(data, dict):
        return data
    result: dict[str, Any] = {}
    for key, value in data.items():
        if key == "api_key" and isinstance(value, str) and len(value) > 8:
            result[key] = value[:4] + "***" + value[-4:]
        elif isinstance(value, dict):
            result[key] = _mask_secrets(value)
        elif isinstance(value, list):
            result[key] = [_mask_secrets(v) if isinstance(v, dict) else v for v in value]
        else:
            result[key] = value
    return result


class ConfigResponse(BaseModel):
    config: dict
    loaded_at: str
    source: str


class ConfigUpdateRequest(BaseModel):
    config: dict
    validate_only: bool = False


class ValidationResult(BaseModel):
    valid: bool
    errors: list[str] = []
    warnings: list[str] = []


@router.get("", response_model=ConfigResponse)
async def get_config(request: Request) -> ConfigResponse:
    config = request.app.state.config
    loaded_at = getattr(
        request.app.state, "config_loaded_at", datetime.now(timezone.utc)
    ).isoformat()
    data = _mask_secrets(config.model_dump())
    return ConfigResponse(config=data, loaded_at=loaded_at, source="file")


@router.post("/validate", response_model=ValidationResult)
async def validate_config(payload: ConfigUpdateRequest) -> ValidationResult:
    try:
        config = RAGKitConfig.model_validate(payload.config)
        errors = validate_custom(config)
        return ValidationResult(valid=len(errors) == 0, errors=errors)
    except Exception as exc:  # noqa: BLE001
        return ValidationResult(valid=False, errors=[str(exc)])


@router.put("")
async def update_config(payload: ConfigUpdateRequest, request: Request) -> dict:
    validation = await validate_config(payload)
    if not validation.valid:
        raise HTTPException(status_code=400, detail={"errors": validation.errors})

    if payload.validate_only:
        return {"status": "valid", "message": "Configuration is valid"}

    config_path: Path | None = getattr(request.app.state, "config_path", None)
    if not config_path:
        raise HTTPException(status_code=500, detail="Configuration path not configured")

    yaml_content = yaml.safe_dump(payload.config, sort_keys=False)
    config_path.write_text(yaml_content, encoding="utf-8")

    return {
        "status": "updated",
        "message": "Configuration saved. Restart required for some changes.",
        "restart_required": True,
    }


def _restart_server() -> None:
    if platform.system() == "Windows":
        subprocess.Popen([sys.executable] + sys.argv)
        raise SystemExit(0)
    os.execv(sys.executable, [sys.executable] + sys.argv)


@router.post("/apply")
async def apply_config(payload: ConfigUpdateRequest, request: Request) -> dict:
    try:
        config = RAGKitConfig.model_validate(payload.config)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail={"errors": [str(exc)]}) from exc

    if not config.is_configured:
        raise HTTPException(
            status_code=400,
            detail={"errors": ["Configuration incomplete -- all sections must be filled"]},
        )

    errors = validate_custom(config)
    if errors:
        raise HTTPException(status_code=400, detail={"errors": errors})

    config_path: Path | None = getattr(request.app.state, "config_path", None)
    if not config_path:
        raise HTTPException(status_code=500, detail="Configuration path not configured")

    yaml_content = yaml.safe_dump(payload.config, sort_keys=False)
    config_path.write_text(yaml_content, encoding="utf-8")

    async def _delayed_restart() -> None:
        await asyncio.sleep(0.5)
        _restart_server()

    asyncio.create_task(_delayed_restart())

    return {"status": "restarting", "message": "Configuration applied. Server restarting..."}


@router.get("/defaults")
async def get_defaults() -> dict:
    return {
        "ingestion": default_ingestion_config().model_dump(),
        "embedding": default_embedding_config().model_dump(),
        "retrieval": default_retrieval_config().model_dump(),
        "llm": default_llm_config().model_dump(),
        "agents": default_agents_config().model_dump(),
    }


@router.get("/export")
async def export_config(request: Request) -> Response:
    config = request.app.state.config
    yaml_content = yaml.safe_dump(_mask_secrets(config.model_dump()), sort_keys=False)
    return Response(
        content=yaml_content,
        media_type="application/x-yaml",
        headers={"Content-Disposition": "attachment; filename=ragkit.yaml"},
    )
