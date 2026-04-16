"""Tests for the scanner module."""

from pathlib import Path

import pytest

from md_dedupe.config import DedupeConfig
from md_dedupe.core.scanner import Scanner, _parse_frontmatter


FIXTURES = Path(__file__).parent.parent / "integration" / "fixtures"


class TestParseFrontmatter:
    def test_with_frontmatter(self):
        content = "---\ntitle: Hello\n---\nBody text"
        fm, body = _parse_frontmatter(content)
        assert fm == {"title": "Hello"}
        assert body == "Body text"

    def test_without_frontmatter(self):
        content = "Just body text"
        fm, body = _parse_frontmatter(content)
        assert fm == {}
        assert body == "Just body text"

    def test_empty_frontmatter(self):
        content = "---\n---\nBody"
        fm, body = _parse_frontmatter(content)
        assert fm == {}
        assert body == "Body"

    def test_multiline_frontmatter(self):
        content = "---\ntitle: Test\ndate: 2026-01-01\ntags:\n  - a\n  - b\n---\nContent"
        fm, body = _parse_frontmatter(content)
        assert fm["title"] == "Test"
        assert body == "Content"


class TestScanner:
    def test_scan_fixtures(self):
        config = DedupeConfig()
        scanner = Scanner()
        files = scanner.scan(FIXTURES, config)
        assert len(files) >= 8  # a through h

    def test_scan_with_min_size(self):
        config = DedupeConfig(min_size=50)
        scanner = Scanner()
        files = scanner.scan(FIXTURES, config)
        # h.md is very short, should be excluded
        for f in files:
            assert f.size >= 50

    def test_scan_single_file(self, tmp_path):
        md = tmp_path / "test.md"
        md.write_text("---\ntitle: Test\n---\nBody")
        config = DedupeConfig()
        scanner = Scanner()
        files = scanner.scan(md, config)
        assert len(files) == 1
        assert files[0].frontmatter == {"title": "Test"}

    def test_scan_excludes_hidden_dirs(self, tmp_path):
        hidden = tmp_path / ".hidden"
        hidden.mkdir()
        (hidden / "secret.md").write_text("secret")
        (tmp_path / "visible.md").write_text("visible")
        config = DedupeConfig()
        scanner = Scanner()
        files = scanner.scan(tmp_path, config)
        assert len(files) == 1
        assert files[0].body == "visible"

    def test_scan_handles_unicode(self, tmp_path):
        md = tmp_path / "unicode.md"
        md.write_text("---\ntitle: テスト\n---\n日本語の本文", encoding="utf-8")
        config = DedupeConfig()
        scanner = Scanner()
        files = scanner.scan(tmp_path, config)
        assert len(files) == 1
        assert "日本語" in files[0].body

    def test_file_info_has_metadata(self):
        config = DedupeConfig()
        scanner = Scanner()
        files = scanner.scan(FIXTURES, config)
        for f in files:
            assert f.path.exists()
            assert f.size > 0
            assert isinstance(f.frontmatter, dict)
