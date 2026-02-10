"""API endpoints for the configuration wizard."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from ragkit.config.wizard import WizardAnalysis, WizardAnswers, analyze_answers
from ragkit.utils.hardware import detect_gpu, detect_ollama

router = APIRouter(prefix="/wizard")
logger = logging.getLogger(__name__)


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
