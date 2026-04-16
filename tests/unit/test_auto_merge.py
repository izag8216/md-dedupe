"""Tests for the auto merge module."""

from pathlib import Path

import pytest

from md_dedupe.merge.auto_merge import auto_merge, merge_body, merge_frontmatter
from md_dedupe.models import DuplicateGroup, FileInfo


class TestMergeFrontmatter:
    def test_union_of_fields(self):
        files = [
            FileInfo(path=Path("a.md"), size=100, frontmatter={"title": "A", "date": "2026"}),
            FileInfo(path=Path("b.md"), size=100, frontmatter={"title": "B", "source": "url"}),
        ]
        merged = merge_frontmatter(files)
        assert "title" in merged
        assert "date" in merged
        assert "source" in merged

    def test_conflict_uses_most_fields(self):
        files = [
            FileInfo(path=Path("rich.md"), size=100, frontmatter={"title": "Rich", "a": 1, "b": 2}),
            FileInfo(path=Path("poor.md"), size=100, frontmatter={"title": "Poor"}),
        ]
        merged = merge_frontmatter(files)
        assert merged["title"] == "Rich"

    def test_empty_frontmatter(self):
        files = [
            FileInfo(path=Path("a.md"), size=100, frontmatter={}),
            FileInfo(path=Path("b.md"), size=100, frontmatter={}),
        ]
        merged = merge_frontmatter(files)
        assert merged == {}


class TestMergeBody:
    def test_unique_lines_preserved(self):
        files = [
            FileInfo(path=Path("a.md"), size=100, body="line1\nline2\nline3"),
            FileInfo(path=Path("b.md"), size=100, body="line2\nline4\nline5"),
        ]
        merged = merge_body(files)
        assert "line1" in merged
        assert "line4" in merged
        assert "line5" in merged

    def test_duplicate_lines_removed(self):
        files = [
            FileInfo(path=Path("a.md"), size=100, body="same\nunique_a"),
            FileInfo(path=Path("b.md"), size=100, body="same\nunique_b"),
        ]
        merged = merge_body(files)
        # "same" should appear only once
        assert merged.count("same") == 1


class TestAutoMerge:
    def test_creates_merged_file(self, tmp_path):
        f1 = tmp_path / "a.md"
        f1.write_text("---\ntitle: A\n---\nContent A")
        f2 = tmp_path / "b.md"
        f2.write_text("---\ntitle: B\n---\nContent B")

        files = [
            FileInfo(path=f1, size=f1.stat().st_size, frontmatter={"title": "A"}, body="Content A"),
            FileInfo(path=f2, size=f2.stat().st_size, frontmatter={"title": "B"}, body="Content B"),
        ]
        group = DuplicateGroup(group_id=0, files=files, duplicate_type="exact", representative=files[0])

        result = auto_merge(group)
        assert result.exists()
        content = result.read_text()
        assert "Content A" in content
        assert "Content B" in content

    def test_creates_backup(self, tmp_path):
        f1 = tmp_path / "a.md"
        f1.write_text("content A")
        f2 = tmp_path / "b.md"
        f2.write_text("content B")

        files = [
            FileInfo(path=f1, size=f1.stat().st_size, body="content A"),
            FileInfo(path=f2, size=f2.stat().st_size, body="content B"),
        ]
        group = DuplicateGroup(group_id=0, files=files, duplicate_type="exact", representative=files[0])

        auto_merge(group, backup=True)

        assert (tmp_path / "a.md.bak").exists()
        assert (tmp_path / "b.md.bak").exists()

    def test_custom_output_path(self, tmp_path):
        f1 = tmp_path / "a.md"
        f1.write_text("content")
        files = [FileInfo(path=f1, size=f1.stat().st_size, body="content")]
        group = DuplicateGroup(group_id=0, files=files, duplicate_type="exact", representative=files[0])

        output = tmp_path / "merged" / "result.md"
        result = auto_merge(group, output_path=output)
        assert result == output
        assert output.exists()
