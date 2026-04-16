"""Integration tests for the scan flow."""

from pathlib import Path

import pytest

from md_dedupe.config import DedupeConfig
from md_dedupe.core.cluster import merge_groups
from md_dedupe.core.frontmatter_cmp import find_frontmatter_duplicates
from md_dedupe.core.hasher import find_exact_duplicates
from md_dedupe.core.scanner import Scanner
from md_dedupe.core.similarity import find_near_duplicates
from md_dedupe.core.url_extractor import find_url_duplicates

FIXTURES = Path(__file__).parent / "fixtures"


class TestScanFlow:
    """Full scan flow integration tests."""

    def test_scan_finds_all_files(self):
        config = DedupeConfig()
        scanner = Scanner()
        files = scanner.scan(FIXTURES, config)
        assert len(files) >= 8

    def test_exact_duplicates_detected(self):
        config = DedupeConfig()
        scanner = Scanner()
        files = scanner.scan(FIXTURES, config)
        groups = find_exact_duplicates(files)

        # a.md and b.md have identical bodies
        assert len(groups) >= 1
        exact_group = groups[0]
        assert len(exact_group.files) == 2
        paths = {f.path.name for f in exact_group.files}
        assert "a.md" in paths
        assert "b.md" in paths

    def test_near_duplicates_detected(self):
        config = DedupeConfig(threshold=0.6)
        scanner = Scanner()
        files = scanner.scan(FIXTURES, config)

        near_groups = find_near_duplicates(files, threshold=0.6)
        # c.md and d.md are near-duplicates
        all_near_files = set()
        for g in near_groups:
            for f in g.files:
                all_near_files.add(f.path.name)

        assert "c.md" in all_near_files or "d.md" in all_near_files

    def test_url_duplicates_detected(self):
        config = DedupeConfig(check_urls=True)
        scanner = Scanner()
        files = scanner.scan(FIXTURES, config)

        url_groups = find_url_duplicates(files, overlap_threshold=0.8)
        # f.md and g.md share the same URLs
        all_url_files = set()
        for g in url_groups:
            for f in g.files:
                all_url_files.add(f.path.name)

        assert "f.md" in all_url_files
        assert "g.md" in all_url_files

    def test_merged_detection(self):
        config = DedupeConfig(check_urls=True, check_frontmatter=True)
        scanner = Scanner()
        files = scanner.scan(FIXTURES, config)

        all_groups = []
        exact = find_exact_duplicates(files)
        if exact:
            all_groups.append(exact)
        near = find_near_duplicates(files, threshold=config.threshold)
        if near:
            all_groups.append(near)
        url = find_url_duplicates(files)
        if url:
            all_groups.append(url)
        fm = find_frontmatter_duplicates(files)
        if fm:
            all_groups.append(fm)

        merged = merge_groups(all_groups)
        # Should have at least exact and url groups
        assert len(merged) >= 2

    def test_min_size_filter(self):
        config = DedupeConfig(min_size=50)
        scanner = Scanner()
        files = scanner.scan(FIXTURES, config)
        # h.md is very short and should be excluded
        for f in files:
            assert f.size >= 50
