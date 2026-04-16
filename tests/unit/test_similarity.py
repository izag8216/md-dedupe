"""Tests for the similarity module."""

from pathlib import Path

import pytest

from md_dedupe.core.similarity import (
    extract_ngrams,
    jaccard_similarity,
    normalize_text,
    pre_filter_by_size,
)
from md_dedupe.models import FileInfo


class TestNormalizeText:
    def test_lowercase(self):
        assert normalize_text("Hello WORLD") == "hello world"

    def test_strip_punctuation(self):
        result = normalize_text("Hello, World!")
        assert "," not in result
        assert "!" not in result

    def test_collapse_whitespace(self):
        assert normalize_text("Hello   World") == "hello world"


class TestExtractNgrams:
    def test_basic_ngrams(self):
        ngrams = extract_ngrams("abc", n=3)
        assert ngrams == {"abc"}

    def test_longer_text(self):
        ngrams = extract_ngrams("abcd", n=3)
        assert ngrams == {"abc", "bcd"}

    def test_short_text(self):
        ngrams = extract_ngrams("ab", n=3)
        assert ngrams == set()

    def test_empty_text(self):
        ngrams = extract_ngrams("", n=3)
        assert ngrams == set()


class TestJaccardSimilarity:
    def test_identical_sets(self):
        s = {"a", "b", "c"}
        assert jaccard_similarity(s, s) == 1.0

    def test_disjoint_sets(self):
        assert jaccard_similarity({"a"}, {"b"}) == 0.0

    def test_partial_overlap(self):
        sim = jaccard_similarity({"a", "b", "c"}, {"b", "c", "d"})
        assert 0.0 < sim < 1.0
        assert abs(sim - 2 / 4) < 0.01  # 2 shared, 4 total

    def test_empty_sets(self):
        assert jaccard_similarity(set(), set()) == 0.0

    def test_one_empty(self):
        assert jaccard_similarity({"a"}, set()) == 0.0


class TestPreFilterBySize:
    def test_similar_sizes_paired(self):
        files = [
            FileInfo(path=f"f{i}.md", size=100 + i * 5, body="")
            for i in range(5)
        ]
        pairs = pre_filter_by_size(files, tolerance=0.2)
        assert len(pairs) > 0

    def test_very_different_sizes_excluded(self):
        files = [
            FileInfo(path=Path("small.md"), size=100, body=""),
            FileInfo(path=Path("large.md"), size=10000, body=""),
        ]
        pairs = pre_filter_by_size(files, tolerance=0.2)
        assert len(pairs) == 0

    def test_single_file(self):
        files = [FileInfo(path=Path("only.md"), size=100, body="")]
        pairs = pre_filter_by_size(files, tolerance=0.2)
        assert len(pairs) == 0
