"""Configuration loader for md-dedupe."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class DedupeConfig(BaseModel):
    """Configuration for deduplication scan."""

    threshold: float = 0.8
    ngram_size: int = 3
    check_urls: bool = False
    check_frontmatter: bool = False
    min_size: int = 0
    exclude: list[str] = Field(
        default_factory=lambda: [".git", ".obsidian", "node_modules", "__pycache__", ".venv"]
    )
    url_overlap: float = 0.8
    frontmatter_fields: list[str] = Field(
        default_factory=lambda: ["title", "date", "source"]
    )

    @classmethod
    def from_toml(cls, path: Path) -> DedupeConfig:
        """Load config from .md-dedupe.toml file."""
        if not path.exists():
            return cls()

        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore[no-redef]

        with open(path, "rb") as f:
            data = tomllib.load(f)

        tool_data = data.get("tool", {}).get("md-dedupe", data)
        return cls(**{k: v for k, v in tool_data.items() if k in cls.model_fields})

    @classmethod
    def find_config(cls, scan_path: Path) -> DedupeConfig:
        """Search for config file starting from scan_path upward."""
        current = scan_path.resolve()
        while True:
            config_path = current / ".md-dedupe.toml"
            if config_path.exists():
                return cls.from_toml(config_path)
            parent = current.parent
            if parent == current:
                break
            current = parent
        return cls()
