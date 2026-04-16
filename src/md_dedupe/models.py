"""Data models for md-dedupe."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class FileInfo(BaseModel):
    """Metadata about a scanned markdown file."""

    path: Path
    size: int
    frontmatter: dict = Field(default_factory=dict)
    body: str = ""
    body_hash: str = ""
    urls: list[str] = Field(default_factory=list)
    modified_time: datetime = datetime.now()


class DuplicateGroup(BaseModel):
    """A group of duplicate or near-duplicate files."""

    group_id: int
    files: list[FileInfo]
    duplicate_type: Literal["exact", "near", "url", "frontmatter"]
    similarity: float | None = None
    representative: FileInfo | None = None


class ScanResult(BaseModel):
    """Complete result of a deduplication scan."""

    path: Path
    total_files: int
    groups: list[DuplicateGroup] = Field(default_factory=list)
    scan_time_seconds: float = 0.0
    config: dict = Field(default_factory=dict)

    @property
    def duplicate_file_count(self) -> int:
        """Total number of files involved in duplicate groups."""
        return sum(len(g.files) for g in self.groups)

    @property
    def space_savings_estimate(self) -> int:
        """Estimated bytes saved if duplicates are removed."""
        total = 0
        for group in self.groups:
            if group.representative:
                total += sum(f.size for f in group.files if f.path != group.representative.path)
            else:
                total += sum(f.size for f in group.files[1:])
        return total
