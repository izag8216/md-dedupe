"""Integration tests for the merge flow."""

from pathlib import Path

import pytest

from md_dedupe.config import DedupeConfig
from md_dedupe.core.hasher import find_exact_duplicates
from md_dedupe.core.scanner import Scanner
from md_dedupe.merge.auto_merge import auto_merge
from md_dedupe.models import DuplicateGroup


FIXTURES = Path(__file__).parent / "fixtures"


class TestMergeFlow:
    """Integration tests for merging duplicate files."""

    def test_merge_exact_duplicates(self, tmp_path):
        """Create duplicates in tmp_path, merge them, verify result."""
        # Create test files with identical bodies
        shared_body = "Shared content line one\nShared content line two\n"
        (tmp_path / "a.md").write_text(f"---\ntitle: Original\n---\n{shared_body}")
        (tmp_path / "b.md").write_text(f"---\ntitle: Copy\nextra: field\n---\n{shared_body}")

        config = DedupeConfig()
        scanner = Scanner()
        files = scanner.scan(tmp_path, config)

        groups = find_exact_duplicates(files)
        assert len(groups) == 1

        group = groups[0]
        result_path = auto_merge(group, backup=True)

        # Verify merged file exists
        assert result_path.exists()

        # Verify merged content
        content = result_path.read_text()
        assert "Shared content" in content

    def test_backup_created(self, tmp_path):
        """Verify .bak files are created during merge."""
        (tmp_path / "x.md").write_text("content x")
        (tmp_path / "y.md").write_text("content x")

        config = DedupeConfig()
        scanner = Scanner()
        files = scanner.scan(tmp_path, config)
        groups = find_exact_duplicates(files)

        assert len(groups) == 1
        auto_merge(groups[0], backup=True)

        assert (tmp_path / "x.md.bak").exists()
        assert (tmp_path / "y.md.bak").exists()

    def test_merge_to_custom_path(self, tmp_path):
        """Merge to a custom output path."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "a.md").write_text("content a")
        (tmp_path / "src" / "b.md").write_text("content a")

        config = DedupeConfig()
        scanner = Scanner()
        files = scanner.scan(tmp_path / "src", config)
        groups = find_exact_duplicates(files)

        output = tmp_path / "merged.md"
        result = auto_merge(groups[0], output_path=output, backup=False)

        assert result == output
        assert output.exists()
        content = output.read_text()
        assert "content a" in content
