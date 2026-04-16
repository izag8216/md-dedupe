"""URL extraction and comparison for deduplication."""

from __future__ import annotations

import re
from collections import defaultdict

from md_dedupe.models import DuplicateGroup, FileInfo

URL_PATTERN = re.compile(r"https?://[^\s<>\"')\]]+", re.IGNORECASE)


def extract_urls(text: str) -> list[str]:
    """Extract and normalize URLs from text.

    Normalizes: strip trailing slashes, remove fragment identifiers.
    Only returns unique URLs.
    """
    raw_urls = URL_PATTERN.findall(text)
    normalized: list[str] = []
    seen: set[str] = set()

    for url in raw_urls:
        # Strip trailing punctuation that's likely not part of URL
        url = url.rstrip(".,;:)")
        # Remove fragment
        url = url.split("#")[0]
        # Strip trailing slash
        url = url.rstrip("/")

        if url not in seen:
            seen.add(url)
            normalized.append(url)

    return normalized


def compute_url_overlap(urls_a: list[str], urls_b: list[str]) -> float:
    """Compute URL overlap ratio between two lists.

    Returns |intersection| / max(|a|, |b|). Returns 0.0 if both empty.
    """
    if not urls_a and not urls_b:
        return 0.0

    set_a = set(urls_a)
    set_b = set(urls_b)
    intersection = set_a & set_b
    max_count = max(len(set_a), len(set_b))

    if max_count == 0:
        return 0.0

    return len(intersection) / max_count


def find_url_duplicates(
    files: list[FileInfo],
    overlap_threshold: float = 0.8,
) -> list[DuplicateGroup]:
    """Find files that share a significant portion of URLs.

    Builds a URL->file index for efficient lookup, then compares
    only pairs sharing at least one URL.
    """
    # Extract URLs for all files
    url_to_files: dict[str, list[int]] = defaultdict(list)
    file_urls: dict[int, list[str]] = {}

    for i, f in enumerate(files):
        urls = extract_urls(f.body)
        f.urls = urls
        file_urls[i] = urls
        for url in urls:
            url_to_files[url].append(i)

    # Find candidate pairs (files sharing at least 1 URL)
    candidate_pairs: set[tuple[int, int]] = set()
    for file_indices in url_to_files.values():
        if len(file_indices) >= 2:
            for i in range(len(file_indices)):
                for j in range(i + 1, len(file_indices)):
                    a, b = file_indices[i], file_indices[j]
                    candidate_pairs.add((min(a, b), max(a, b)))

    # Evaluate candidates
    groups: list[DuplicateGroup] = []
    used: set[int] = set()

    for a_idx, b_idx in sorted(candidate_pairs):
        overlap = compute_url_overlap(file_urls[a_idx], file_urls[b_idx])
        if overlap >= overlap_threshold:
            if a_idx in used and b_idx in used:
                continue
            groups.append(
                DuplicateGroup(
                    group_id=len(groups),
                    files=[files[a_idx], files[b_idx]],
                    duplicate_type="url",
                    similarity=round(overlap, 4),
                    representative=files[a_idx],
                )
            )
            used.add(a_idx)
            used.add(b_idx)

    return groups
