"""Near-duplicate detection via n-gram Jaccard similarity."""

from __future__ import annotations

from md_dedupe.models import DuplicateGroup, FileInfo


def normalize_text(text: str) -> str:
    """Normalize text for comparison: lowercase, collapse whitespace, strip punctuation."""
    import re

    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def extract_ngrams(text: str, n: int = 3) -> set[str]:
    """Extract character n-grams from normalized text."""
    normalized = normalize_text(text)
    if len(normalized) < n:
        return set()
    return {normalized[i : i + n] for i in range(len(normalized) - n + 1)}


def jaccard_similarity(set_a: set[str], set_b: set[str]) -> float:
    """Compute Jaccard similarity between two sets."""
    if not set_a and not set_b:
        return 0.0
    union = set_a | set_b
    if not union:
        return 0.0
    intersection = set_a & set_b
    return len(intersection) / len(union)


def pre_filter_by_size(
    files: list[FileInfo], tolerance: float = 0.2
) -> list[tuple[FileInfo, FileInfo]]:
    """Generate candidate pairs within tolerance% size difference.

    Sorts by size and uses a sliding window for efficiency.
    """
    if len(files) < 2:
        return []

    sorted_files = sorted(files, key=lambda f: f.size)
    pairs: list[tuple[FileInfo, FileInfo]] = []

    for i in range(len(sorted_files)):
        for j in range(i + 1, len(sorted_files)):
            a = sorted_files[i]
            b = sorted_files[j]
            if a.size == 0:
                continue
            ratio = abs(a.size - b.size) / max(a.size, b.size)
            if ratio > tolerance:
                break  # sorted, so all subsequent are larger
            pairs.append((a, b))

    return pairs


def find_near_duplicates(
    files: list[FileInfo],
    threshold: float = 0.8,
    ngram_size: int = 3,
) -> list[DuplicateGroup]:
    """Find near-duplicate files using n-gram Jaccard similarity.

    Skips files under 50 characters or with empty bodies.
    Uses size pre-filter to avoid O(n^2) comparisons.
    """
    # Filter out too-short files
    eligible = [f for f in files if len(f.body.strip()) >= 50]

    candidates = pre_filter_by_size(eligible)
    if not candidates:
        return []

    # Pre-compute ngrams
    ngram_cache: dict[int, set[str]] = {}
    for f in eligible:
        ngram_cache[id(f)] = extract_ngrams(f.body, ngram_size)

    # Find similar pairs
    similar_pairs: list[tuple[FileInfo, FileInfo, float]] = []
    for a, b in candidates:
        ngrams_a = ngram_cache[id(a)]
        ngrams_b = ngram_cache[id(b)]
        sim = jaccard_similarity(ngrams_a, ngrams_b)
        if sim >= threshold:
            similar_pairs.append((a, b, sim))

    if not similar_pairs:
        return []

    # Group connected pairs using simple clustering
    groups = _cluster_pairs(similar_pairs)
    return groups


def _cluster_pairs(
    pairs: list[tuple[FileInfo, FileInfo, float]],
) -> list[DuplicateGroup]:
    """Cluster similar file pairs into groups using union-find."""
    from md_dedupe.core.cluster import UnionFind

    file_ids: dict[int, int] = {}
    all_files: dict[int, FileInfo] = {}
    idx = 0

    for a, b, _sim in pairs:
        if id(a) not in file_ids:
            file_ids[id(a)] = idx
            all_files[idx] = a
            idx += 1
        if id(b) not in file_ids:
            file_ids[id(b)] = idx
            all_files[idx] = b
            idx += 1

    uf = UnionFind(idx)
    # Track best similarity per pair
    pair_sim: dict[tuple[int, int], float] = {}
    for a, b, sim in pairs:
        ia = file_ids[id(a)]
        ib = file_ids[id(b)]
        key = (min(ia, ib), max(ia, ib))
        pair_sim[key] = max(pair_sim.get(key, 0.0), sim)
        uf.union(ia, ib)

    # Build groups from connected components
    components = uf.groups()
    result: list[DuplicateGroup] = []
    group_id = 0

    for members in components.values():
        if len(members) < 2:
            continue
        group_files = [all_files[m] for m in members]
        # Average similarity for the group
        sims = []
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                key = (min(members[i], members[j]), max(members[i], members[j]))
                if key in pair_sim:
                    sims.append(pair_sim[key])
        avg_sim = sum(sims) / len(sims) if sims else threshold

        result.append(
            DuplicateGroup(
                group_id=group_id,
                files=group_files,
                duplicate_type="near",
                similarity=round(avg_sim, 4),
                representative=max(group_files, key=lambda f: len(f.body)),
            )
        )
        group_id += 1

    return result
