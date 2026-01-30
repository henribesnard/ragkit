"""Admin configuration endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import yaml  # type: ignore[import-untyped]
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel

from ragkit.config.schema import RAGKitConfig
from ragkit.config.validators import validate_config as validate_custom

router = APIRouter(prefix="/config")


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
    return ConfigResponse(config=config.model_dump(), loaded_at=loaded_at, source="file")


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


@router.get("/export")
async def export_config(request: Request) -> Response:
    config = request.app.state.config
    yaml_content = yaml.safe_dump(config.model_dump(), sort_keys=False)
    return Response(
        content=yaml_content,
        media_type="application/x-yaml",
        headers={"Content-Disposition": "attachment; filename=ragkit.yaml"},
    )
