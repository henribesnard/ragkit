"""Configuration loader and validation utilities."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from ragkit.config.schema import RAGKitConfig
from ragkit.config.validators import validate_config
from ragkit.exceptions import ConfigError


class ConfigLoader:
    """Load and validate YAML configuration files."""

    def load(self, path: Path) -> RAGKitConfig:
        data = self._read_yaml(path)
        config = RAGKitConfig.model_validate(data)
        self._raise_if_errors(config)
        return config

    def load_with_env(self, path: Path) -> RAGKitConfig:
        data = self._read_yaml(path)
        resolved = self._resolve_env_vars(data)
        config = RAGKitConfig.model_validate(resolved)
        self._raise_if_errors(config)
        return config

    def validate(self, config: RAGKitConfig) -> list[str]:
        return validate_config(config)

    def _raise_if_errors(self, config: RAGKitConfig) -> None:
        errors = self.validate(config)
        if errors:
            message = "Invalid configuration:\n- " + "\n- ".join(errors)
            raise ConfigError(message)

    def _read_yaml(self, path: Path) -> dict[str, Any]:
        if not Path(path).exists():
            raise ConfigError(f"Config file not found: {path}")
        try:
            with Path(path).open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}
        except yaml.YAMLError as exc:
            raise ConfigError(f"Invalid YAML: {exc}") from exc
        if not isinstance(data, dict):
            raise ConfigError("Config root must be a YAML mapping")
        return data

    def _resolve_env_vars(self, data: Any) -> Any:
        if isinstance(data, dict):
            resolved = {key: self._resolve_env_vars(value) for key, value in data.items()}
            for key, value in list(resolved.items()):
                if key.endswith("_env") and isinstance(value, str):
                    env_value = os.getenv(value)
                    if env_value is None:
                        raise ConfigError(f"Missing environment variable: {value}")
                    target_key = key[:-4]
                    if resolved.get(target_key) in (None, ""):
                        resolved[target_key] = env_value
            return resolved
        if isinstance(data, list):
            return [self._resolve_env_vars(item) for item in data]
        return data
