"""Configuration loading for the pipeline.

Configuration is a plain dictionary loaded from JSON. There is deliberately
no schema library in use here -- see docs/conventions.md for why the team
prefers explicit validation functions over a config framework.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_CONFIG: dict[str, Any] = {
    "source_path": "data/sample_records.csv",
    "writer": {
        "type": "local",
        "output_dir": "output",
    },
}


class ConfigError(Exception):
    """Raised when pipeline configuration is missing or invalid."""


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load pipeline configuration from a JSON file.

    If `path` is None, the default configuration is returned as-is. If a
    path is given, the file is loaded and merged over the defaults so callers
    only need to specify the keys they want to override.

    Args:
        path: Path to a JSON configuration file, or None to use defaults.

    Returns:
        The resolved configuration dictionary.

    Raises:
        ConfigError: If the file exists but cannot be parsed, or a required
            key is missing after merging.
    """
    config = {**DEFAULT_CONFIG, "writer": dict(DEFAULT_CONFIG["writer"])}

    if path is not None:
        config_path = Path(path)
        if not config_path.exists():
            raise ConfigError(f"Configuration file not found: {config_path}")

        try:
            overrides = json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ConfigError(f"Invalid JSON in {config_path}: {exc}") from exc

        writer_overrides = overrides.pop("writer", None)
        config.update(overrides)
        if writer_overrides:
            config["writer"].update(writer_overrides)

    _validate(config)
    return config


def _validate(config: dict[str, Any]) -> None:
    if not config.get("source_path"):
        raise ConfigError("Configuration is missing required key: source_path")

    writer_config = config.get("writer")
    if not writer_config or "type" not in writer_config:
        raise ConfigError("Configuration is missing required key: writer.type")
