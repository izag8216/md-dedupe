"""Union-find clustering for merging detection results."""

from __future__ import annotations

from md_dedupe.models import DuplicateGroup, FileInfo


class UnionFind:
    """Union-Find (Disjoint Set Union) data structure."""

    def __init__(self, n: int) -> None:
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        """Find root of element x with path compression."""
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: int, y: int) -> None:
        """Union two elements by rank."""
        rx = self.find(x)
        ry = self.find(y)
        if rx == ry:
            return
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1

    def connected(self, x: int, y: int) -> bool:
        """Check if two elements are in the same set."""
        return self.find(x) == self.find(y)

    def groups(self) -> dict[int, list[int]]:
        """Return all groups as {root: [members]}."""
        result: dict[int, list[int]] = {}
        for i in range(len(self.parent)):
            root = self.find(i)
            if root not in result:
                result[root] = []
            result[root].append(i)
        return result


TYPE_PRIORITY = {"exact": 0, "near": 1, "url": 2, "frontmatter": 3}


def select_representative(files: list[FileInfo]) -> FileInfo:
    """Select the best representative file from a group.

    Priority: most frontmatter fields, then longest body, then earliest modified.
    """
    return max(
        files,
        key=lambda f: (len(f.frontmatter), len(f.body), -f.modified_time.timestamp()),
    )


def merge_groups(all_groups: list[list[DuplicateGroup]]) -> list[DuplicateGroup]:
    """Merge duplicate groups from different detection methods using UnionFind.

    When groups overlap (share files), they are merged. The duplicate_type
    is set to the highest-priority type among merged groups.
    """
    # Flatten all groups
    flat: list[DuplicateGroup] = []
    for group_list in all_groups:
        flat.extend(group_list)

    if not flat:
        return []

    # Map file paths to indices
    file_index: dict[str, int] = {}
    files_by_idx: dict[int, FileInfo] = {}
    idx = 0

    for group in flat:
        for f in group.files:
            key = str(f.path)
            if key not in file_index:
                file_index[key] = idx
                files_by_idx[idx] = f
                idx += 1

    # Union files that appear in the same group
    uf = UnionFind(idx)
    group_type: dict[int, str] = {}  # root -> best type

    for group in flat:
        if len(group.files) < 2:
            continue
        first = file_index[str(group.files[0].path)]
        for f in group.files[1:]:
            other = file_index[str(f.path)]
            uf.union(first, other)

        root = uf.find(first)
        existing = group_type.get(root, "frontmatter")
        if TYPE_PRIORITY.get(group.duplicate_type, 99) < TYPE_PRIORITY.get(existing, 99):
            group_type[root] = group.duplicate_type

    # Build merged groups
    components = uf.groups()
    result: list[DuplicateGroup] = []

    for root, members in components.items():
        if len(members) < 2:
            continue

        group_files = [files_by_idx[m] for m in members]
        # Deduplicate files
        seen: set[str] = set()
        unique_files: list[FileInfo] = []
        for f in group_files:
            key = str(f.path)
            if key not in seen:
                seen.add(key)
                unique_files.append(f)

        if len(unique_files) < 2:
            continue

        rep = select_representative(unique_files)
        dup_type = group_type.get(root, "exact")

        result.append(
            DuplicateGroup(
                group_id=len(result),
                files=unique_files,
                duplicate_type=dup_type,
                similarity=None,
                representative=rep,
            )
        )

    return result
