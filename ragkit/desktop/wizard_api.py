"""API endpoints for the configuration wizard."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ragkit.config.wizard import WizardAnalysis, WizardAnswers, analyze_answers
from ragkit.utils.hardware import detect_gpu, detect_ollama

router = APIRouter(prefix="/wizard")
logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx", ".doc"}


class FolderValidationRequest(BaseModel):
    folder_path: str


def _empty_stats() -> dict[str, Any]:
    return {"files": 0, "size_mb": 0.0, "extensions": [], "extension_counts": {}}


def validate_knowledge_base_folder(folder_path: str) -> dict[str, Any]:
    """Validate that the folder is suitable for a knowledge base."""
    stats = _empty_stats()
    if not folder_path or not folder_path.strip():
        return {
            "valid": False,
            "error": "Folder path is required",
            "error_code": "required",
            "stats": stats,
        }

    path = Path(folder_path)
    if not path.exists():
        return {
            "valid": False,
            "error": "Folder does not exist",
            "error_code": "not_exists",
            "stats": stats,
        }
    if not path.is_dir():
        return {
            "valid": False,
            "error": "Path is not a directory",
            "error_code": "not_dir",
            "stats": stats,
        }
    if not os.access(path, os.R_OK):
        return {
            "valid": False,
            "error": "No read permission for this folder",
            "error_code": "no_permission",
            "stats": stats,
        }

    extension_counts: dict[str, int] = {}
    total_size = 0
    try:
        for file_path in path.rglob("*"):
            if not file_path.is_file():
                continue
            ext = file_path.suffix.lower()
            if ext not in SUPPORTED_EXTENSIONS:
                continue
            total_size += file_path.stat().st_size
            ext_key = ext.lstrip(".")
            extension_counts[ext_key] = extension_counts.get(ext_key, 0) + 1
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to scan folder %s: %s", folder_path, exc)
        return {
            "valid": False,
            "error": "Error scanning folder",
            "error_code": "scan_error",
            "stats": stats,
        }

    total_files = sum(extension_counts.values())
    if total_files == 0:
        return {
            "valid": False,
            "error": "No supported documents found in folder",
            "error_code": "no_supported_files",
            "stats": stats,
        }

    stats = {
        "files": total_files,
        "size_mb": round(total_size / (1024 * 1024), 2),
        "extensions": sorted(extension_counts.keys()),
        "extension_counts": extension_counts,
    }
    return {"valid": True, "error": None, "error_code": None, "stats": stats}


@router.post("/analyze-profile", response_model=WizardAnalysis)
async def analyze_profile(answers: WizardAnswers) -> WizardAnalysis:
    """Analyze wizard answers and return the recommended profile."""
    try:
        logger.info("Analyzing wizard profile for kb_type=%s", answers.kb_type)
        result = analyze_answers(answers)
        logger.debug("Wizard profile summary: %s", result.config_summary)
        return result
    except ValueError as exc:
        logger.warning("Wizard profile analysis failed: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/environment-detection")
async def detect_environment() -> dict:
    """Detect GPU and Ollama environment information."""
    logger.info("Detecting wizard environment")
    gpu_info = detect_gpu()
    ollama_status = await detect_ollama()

    return {
        "gpu": {
            "detected": gpu_info.detected,
            "name": gpu_info.name,
            "vram_total_gb": gpu_info.vram_total_gb,
            "vram_free_gb": gpu_info.vram_free_gb,
        },
        "ollama": {
            "installed": ollama_status.installed,
            "running": ollama_status.running,
            "version": ollama_status.version,
            "models": ollama_status.models,
        },
    }


@router.post("/validate-folder")
async def validate_folder(request: FolderValidationRequest) -> dict[str, Any]:
    """Validate a folder for knowledge base creation."""
    return validate_knowledge_base_folder(request.folder_path)
