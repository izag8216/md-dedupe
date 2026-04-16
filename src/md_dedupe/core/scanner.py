"""Directory scanner for markdown files."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import yaml

from md_dedupe.config import DedupeConfig
from md_dedupe.models import FileInfo


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from markdown content.

    Returns (frontmatter_dict, body_string).
    """
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    try:
        fm = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return {}, content

    body = parts[2].strip()
    return fm, body


def _should_exclude(path: Path, exclude: list[str]) -> bool:
    """Check if path should be excluded based on patterns."""
    parts = path.parts
    for pattern in exclude:
        for part in parts:
            if pattern in part:
                return True
    # Skip hidden files and directories
    for part in parts:
        if part.startswith(".") and part not in (".", ".."):
            return True
    return False


class Scanner:
    """Walks directories and collects markdown file metadata."""

    def scan(self, path: Path, config: DedupeConfig) -> list[FileInfo]:
        """Scan directory for .md files and collect metadata.

        Args:
            path: Root directory to scan.
            config: Scan configuration.

        Returns:
            List of FileInfo objects for all discovered markdown files.
        """
        root = path.resolve()
        if not root.is_dir():
            if root.is_file() and root.suffix == ".md":
                return [self._process_file(root, config)]
            return []

        files: list[FileInfo] = []
        for md_file in sorted(root.rglob("*.md")):
            if _should_exclude(md_file.relative_to(root), config.exclude):
                continue
            if md_file.stat().st_size < config.min_size:
                continue
            info = self._process_file(md_file, config)
            if info is not None:
                files.append(info)

        return files

    def _process_file(self, path: Path, config: DedupeConfig) -> FileInfo | None:
        """Process a single markdown file."""
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            return None

        stat = path.stat()
        frontmatter, body = _parse_frontmatter(content)

        return FileInfo(
            path=path,
            size=stat.st_size,
            frontmatter=frontmatter,
            body=body,
            body_hash="",
            urls=[],
            modified_time=datetime.fromtimestamp(stat.st_mtime),
        )
