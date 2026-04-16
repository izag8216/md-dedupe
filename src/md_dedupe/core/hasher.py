"""SHA-256 exact duplicate detection."""

from __future__ import annotations

import hashlib
from collections import defaultdict

from md_dedupe.models import DuplicateGroup, FileInfo


def compute_hash(body: str) -> str:
    """Compute SHA-256 hash of normalized body text.

    Normalization: strip whitespace, normalize line endings, collapse blank lines.
    """
    normalized = body.strip()
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse multiple blank lines to single
    while "\n\n\n" in normalized:
        normalized = normalized.replace("\n\n\n", "\n\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def find_exact_duplicates(files: list[FileInfo]) -> list[DuplicateGroup]:
    """Group files by body hash. Returns groups with 2+ files.

    Args:
        files: List of FileInfo objects with body content.

    Returns:
        List of DuplicateGroups for exact matches.
    """
    hash_groups: dict[str, list[FileInfo]] = defaultdict(list)

    for f in files:
        body_hash = compute_hash(f.body)
        f.body_hash = body_hash
        hash_groups[body_hash].append(f)

    groups: list[DuplicateGroup] = []
    for group_id, (body_hash, group_files) in enumerate(
        (h, g) for h, g in hash_groups.items() if len(g) >= 2
    ):
        # Enumerate only groups with 2+ files
        groups.append(
            DuplicateGroup(
                group_id=len(groups),
                files=group_files,
                duplicate_type="exact",
                similarity=1.0,
                representative=group_files[0],
            )
        )

    return groups
