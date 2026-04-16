"""Tests for the hasher module."""

from pathlib import Path

import pytest

from md_dedupe.core.hasher import compute_hash, find_exact_duplicates
from md_dedupe.models import FileInfo


class TestComputeHash:
    def test_identical_bodies(self):
        body = "Hello world\nThis is a test"
        assert compute_hash(body) == compute_hash(body)

    def test_different_bodies(self):
        assert compute_hash("Hello") != compute_hash("World")

    def test_whitespace_normalization(self):
        h1 = compute_hash("Hello\nWorld")
        h2 = compute_hash("  Hello\nWorld  ")  # stripped
        assert h1 == h2

    def test_line_ending_normalization(self):
        h1 = compute_hash("Hello\nWorld")
        h2 = compute_hash("Hello\r\nWorld")
        h3 = compute_hash("Hello\rWorld")
        assert h1 == h2 == h3

    def test_empty_body(self):
        h = compute_hash("")
        assert isinstance(h, str)
        assert len(h) == 64  # SHA-256 hex length


class TestFindExactDuplicates:
    def test_finds_exact_duplicates(self):
        files = [
            FileInfo(path=Path("a.md"), size=100, body="same content"),
            FileInfo(path=Path("b.md"), size=100, body="same content"),
            FileInfo(path=Path("c.md"), size=100, body="different"),
        ]
        groups = find_exact_duplicates(files)
        assert len(groups) == 1
        assert len(groups[0].files) == 2
        assert groups[0].duplicate_type == "exact"
        assert groups[0].similarity == 1.0

    def test_no_duplicates(self):
        files = [
            FileInfo(path=Path("a.md"), size=100, body="content A"),
            FileInfo(path=Path("b.md"), size=100, body="content B"),
        ]
        groups = find_exact_duplicates(files)
        assert len(groups) == 0

    def test_multiple_groups(self):
        files = [
            FileInfo(path=Path("a.md"), size=100, body="group1"),
            FileInfo(path=Path("b.md"), size=100, body="group1"),
            FileInfo(path=Path("c.md"), size=100, body="group2"),
            FileInfo(path=Path("d.md"), size=100, body="group2"),
        ]
        groups = find_exact_duplicates(files)
        assert len(groups) == 2

    def test_triple_duplicate(self):
        files = [
            FileInfo(path=Path(f"f{i}.md"), size=100, body="same")
            for i in range(3)
        ]
        groups = find_exact_duplicates(files)
        assert len(groups) == 1
        assert len(groups[0].files) == 3
