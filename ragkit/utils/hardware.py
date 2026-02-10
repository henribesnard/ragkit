"""Hardware detection utilities for the wizard."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass


@dataclass
class GPUInfo:
    """GPU detection result."""

    detected: bool
    name: str | None = None
    vram_total_gb: float | None = None
    vram_free_gb: float | None = None


@dataclass
class OllamaInfo:
    """Ollama detection result."""

    installed: bool
    running: bool
    version: str | None = None
    models: list[str] | None = None

    def __post_init__(self) -> None:
        if self.models is None:
            self.models = []


def detect_gpu() -> GPUInfo:
    """Detect NVIDIA GPU details if available."""
    try:
        import torch

        if torch.cuda.is_available():
            device = torch.cuda.get_device_properties(0)
            total_vram = device.total_memory / (1024**3)
            free_vram = total_vram * 0.8

            return GPUInfo(
                detected=True,
                name=device.name,
                vram_total_gb=round(total_vram, 1),
                vram_free_gb=round(free_vram, 1),
            )
    except ImportError:
        pass
    except Exception:
        pass

    return GPUInfo(detected=False)


async def detect_ollama() -> OllamaInfo:
    """Detect if Ollama is installed and running."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "ollama",
            "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        version = stdout.decode().strip()
    except FileNotFoundError:
        return OllamaInfo(installed=False, running=False)

    try:
        proc = await asyncio.create_subprocess_exec(
            "ollama",
            "list",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()

        if proc.returncode != 0:
            return OllamaInfo(installed=True, running=False, version=version)

        lines = stdout.decode().strip().split("\n")
        models = []
        for line in lines[1:]:
            parts = line.split()
            if parts:
                models.append(parts[0])

        return OllamaInfo(
            installed=True,
            running=True,
            version=version,
            models=models,
        )
    except Exception:
        return OllamaInfo(installed=True, running=False, version=version)
