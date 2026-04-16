"""Safe automatic merge for duplicate groups."""

from __future__ import annotations

import shutil
from pathlib import Path

from md_dedupe.models import DuplicateGroup, FileInfo


def merge_frontmatter(files: list[FileInfo]) -> dict:
    """Merge frontmatter from multiple files by union.

    For conflicts (same key, different value): keep value from file with
    most frontmatter fields, then longest string value.
    """
    merged: dict = {}
    field_sources: dict[str, int] = {}  # field -> file index with most fields

    # Sort files: most frontmatter fields first
    sorted_files = sorted(files, key=lambda f: len(f.frontmatter), reverse=True)

    for i, f in enumerate(sorted_files):
        for key, value in f.frontmatter.items():
            if key not in merged:
                merged[key] = value
                field_sources[key] = i
            else:
                # Conflict: keep from file with more frontmatter fields
                current_source = field_sources[key]
                if len(sorted_files[i].frontmatter) > len(sorted_files[current_source].frontmatter):
                    merged[key] = value
                    field_sources[key] = i
                elif len(sorted_files[i].frontmatter) == len(sorted_files[current_source].frontmatter):
                    # Tie-break: keep longer value
                    if len(str(value)) > len(str(merged[key])):
                        merged[key] = value
                        field_sources[key] = i

    return merged


def merge_body(files: list[FileInfo]) -> str:
    """Merge body content by combining unique lines.

    Keeps all unique lines from the representative file first,
    then appends unique lines from other files.
    """
    # Sort: representative first (longest body), then others
    sorted_files = sorted(files, key=lambda f: len(f.body), reverse=True)

    seen_lines: set[str] = set()
    result_lines: list[str] = []

    for f in sorted_files:
        for line in f.body.split("\n"):
            stripped = line.strip()
            if stripped and stripped not in seen_lines:
                seen_lines.add(stripped)
                result_lines.append(line)
            elif not stripped:
                # Preserve blank lines from representative only
                if f == sorted_files[0] and not result_lines:
                    result_lines.append("")

    return "\n".join(result_lines)


def auto_merge(
    group: DuplicateGroup,
    output_path: Path | None = None,
    backup: bool = True,
) -> Path:
    """Auto-merge a duplicate group into the representative file.

    Args:
        group: Duplicate group to merge.
        output_path: Optional custom output path. If None, overwrites representative.
        backup: If True, creates .bak copies of original files.

    Returns:
        Path to the merged file.
    """
    if group.representative is None:
        rep = max(group.files, key=lambda f: len(f.body))
    else:
        rep = group.representative

    merged_fm = merge_frontmatter(group.files)
    merged_body = merge_body(group.files)

    # Build merged content
    parts: list[str] = []
    if merged_fm:
        import yaml

        parts.append("---")
        parts.append(yaml.dump(merged_fm, allow_unicode=True, default_flow_style=False).strip())
        parts.append("---")
        parts.append("")
    parts.append(merged_body)
    content = "\n".join(parts)

    target = output_path or rep.path

    # Backup original files if requested
    if backup:
        for f in group.files:
            if f.path.exists():
                bak_path = f.path.with_suffix(f.path.suffix + ".bak")
                shutil.copy2(f.path, bak_path)

    # Write merged content
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")

    return target
