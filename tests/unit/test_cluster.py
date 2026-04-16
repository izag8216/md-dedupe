"""Tests for the cluster module."""

from pathlib import Path

import pytest

from md_dedupe.core.cluster import UnionFind, merge_groups, select_representative
from md_dedupe.models import DuplicateGroup, FileInfo


class TestUnionFind:
    def test_initial_state(self):
        uf = UnionFind(3)
        assert uf.find(0) == 0
        assert uf.find(1) == 1
        assert not uf.connected(0, 1)

    def test_union(self):
        uf = UnionFind(3)
        uf.union(0, 1)
        assert uf.connected(0, 1)
        assert not uf.connected(0, 2)

    def test_transitive_union(self):
        uf = UnionFind(4)
        uf.union(0, 1)
        uf.union(1, 2)
        assert uf.connected(0, 2)

    def test_groups(self):
        uf = UnionFind(4)
        uf.union(0, 1)
        uf.union(2, 3)
        g = uf.groups()
        assert len(g) == 2

    def test_single_group(self):
        uf = UnionFind(3)
        uf.union(0, 1)
        uf.union(1, 2)
        g = uf.groups()
        assert len(g) == 1
        assert len(list(g.values())[0]) == 3


class TestSelectRepresentative:
    def test_most_frontmatter(self):
        files = [
            FileInfo(path=Path("few.md"), size=100, frontmatter={"title": "A"}),
            FileInfo(path=Path("best.md"), size=100, frontmatter={"title": "Best", "date": "2026", "extra": "x"}),
            FileInfo(path=Path("short.md"), size=100, frontmatter={}),
        ]
        rep = select_representative(files)
        assert rep.path == Path("best.md")


class TestMergeGroups:
    def test_merge_overlapping_groups(self):
        f1 = FileInfo(path=Path("a.md"), size=100, body="content a")
        f2 = FileInfo(path=Path("b.md"), size=100, body="content b")
        f3 = FileInfo(path=Path("c.md"), size=100, body="content c")

        # Exact group: a, b
        exact = [
            DuplicateGroup(group_id=0, files=[f1, f2], duplicate_type="exact", similarity=1.0),
        ]
        # Near group: b, c
        near = [
            DuplicateGroup(group_id=0, files=[f2, f3], duplicate_type="near", similarity=0.85),
        ]

        merged = merge_groups([exact, near])
        # Should merge into one group since b appears in both
        assert len(merged) == 1
        assert len(merged[0].files) == 3
        assert merged[0].duplicate_type == "exact"  # Higher priority

    def test_empty_input(self):
        assert merge_groups([]) == []

    def test_non_overlapping_groups(self):
        f1 = FileInfo(path=Path("a.md"), size=100, body="a")
        f2 = FileInfo(path=Path("b.md"), size=100, body="b")
        f3 = FileInfo(path=Path("c.md"), size=100, body="c")
        f4 = FileInfo(path=Path("d.md"), size=100, body="d")

        groups = [
            [
                DuplicateGroup(group_id=0, files=[f1, f2], duplicate_type="exact", similarity=1.0),
                DuplicateGroup(group_id=1, files=[f3, f4], duplicate_type="near", similarity=0.9),
            ]
        ]
        merged = merge_groups(groups)
        assert len(merged) == 2
