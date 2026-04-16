"""Tests for the frontmatter comparison module."""

from pathlib import Path

import pytest

from md_dedupe.core.frontmatter_cmp import compare_frontmatter, find_frontmatter_duplicates
from md_dedupe.models import FileInfo


class TestCompareFrontmatter:
    def test_identical_frontmatter(self):
        fm = {"title": "Test", "date": "2026-01-01"}
        sim = compare_frontmatter(fm, fm, fields=["title", "date"])
        assert sim == 1.0

    def test_partial_match(self):
        fm_a = {"title": "Test", "date": "2026-01-01"}
        fm_b = {"title": "Test", "date": "2026-02-01"}
        sim = compare_frontmatter(fm_a, fm_b)
        assert 0.0 < sim < 1.0

    def test_no_match(self):
        fm_a = {"title": "Alpha"}
        fm_b = {"title": "Beta"}
        sim = compare_frontmatter(fm_a, fm_b)
        assert sim == 0.0

    def test_case_insensitive(self):
        fm_a = {"title": "Hello World"}
        fm_b = {"title": "hello world"}
        sim = compare_frontmatter(fm_a, fm_b, fields=["title"])
        assert sim == 1.0

    def test_missing_fields(self):
        fm_a = {"title": "Test"}
        fm_b = {"title": "Test", "date": "2026-01-01"}
        sim = compare_frontmatter(fm_a, fm_b, fields=["title", "date"])
        assert sim == 0.5


class TestFindFrontmatterDuplicates:
    def test_finds_matching_files(self):
        files = [
            FileInfo(path=Path(f"f{i}.md"), size=100, frontmatter={"title": "Same", "date": "2026-01-01", "source": "x"})
            for i in range(3)
        ]
        groups = find_frontmatter_duplicates(files, threshold=0.8)
        assert len(groups) >= 1

    def test_no_matches(self):
        files = [
            FileInfo(path=Path("a.md"), size=100, frontmatter={"title": "A"}),
            FileInfo(path=Path("b.md"), size=100, frontmatter={"title": "B"}),
        ]
        groups = find_frontmatter_duplicates(files)
        assert len(groups) == 0
