"""Frontmatter field comparison for deduplication."""

from __future__ import annotations

from md_dedupe.models import DuplicateGroup, FileInfo


def compare_frontmatter(
    fm_a: dict,
    fm_b: dict,
    fields: list[str] | None = None,
) -> float:
    """Compare frontmatter fields between two files.

    Returns fraction of matching fields (0.0 to 1.0).
    String comparisons are case-insensitive.
    """
    if fields is None:
        fields = ["title", "date", "source"]

    if not fields:
        return 0.0

    matches = 0
    for field in fields:
        val_a = fm_a.get(field)
        val_b = fm_b.get(field)

        if val_a is None or val_b is None:
            continue

        # Normalize for comparison
        str_a = str(val_a).strip().lower()
        str_b = str(val_b).strip().lower()

        if str_a == str_b:
            matches += 1

    return matches / len(fields)


def find_frontmatter_duplicates(
    files: list[FileInfo],
    fields: list[str] | None = None,
    threshold: float = 0.8,
) -> list[DuplicateGroup]:
    """Find files with matching frontmatter fields.

    Compares all pairs on specified frontmatter fields and groups
    those exceeding the threshold.
    """
    if fields is None:
        fields = ["title", "date", "source"]

    # Filter files that have at least one of the target fields
    eligible = [f for f in files if any(k in f.frontmatter for k in fields)]
    if len(eligible) < 2:
        return []

    # Find similar pairs
    similar_pairs: list[tuple[int, int, float]] = []
    for i in range(len(eligible)):
        for j in range(i + 1, len(eligible)):
            sim = compare_frontmatter(
                eligible[i].frontmatter,
                eligible[j].frontmatter,
                fields,
            )
            if sim >= threshold:
                similar_pairs.append((i, j, sim))

    if not similar_pairs:
        return []

    # Simple clustering: greedy grouping
    groups: list[DuplicateGroup] = []
    assigned: set[int] = set()

    for i, j, sim in similar_pairs:
        if i in assigned and j in assigned:
            continue
        group_files = [eligible[i], eligible[j]]
        assigned.add(i)
        assigned.add(j)

        groups.append(
            DuplicateGroup(
                group_id=len(groups),
                files=group_files,
                duplicate_type="frontmatter",
                similarity=round(sim, 4),
                representative=max(group_files, key=lambda f: len(f.frontmatter)),
            )
        )

    return groups
