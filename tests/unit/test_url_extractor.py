"""Tests for the URL extractor module."""

import pytest

from md_dedupe.core.url_extractor import compute_url_overlap, extract_urls
from md_dedupe.models import FileInfo


class TestExtractUrls:
    def test_basic_url(self):
        text = "Visit https://example.com for more"
        urls = extract_urls(text)
        assert "https://example.com" in urls

    def test_multiple_urls(self):
        text = "See https://a.com and https://b.com"
        urls = extract_urls(text)
        assert len(urls) == 2

    def test_strips_trailing_slash(self):
        text = "https://example.com/"
        urls = extract_urls(text)
        assert urls == ["https://example.com"]

    def test_removes_fragment(self):
        text = "https://example.com/page#section"
        urls = extract_urls(text)
        assert urls == ["https://example.com/page"]

    def test_no_urls(self):
        assert extract_urls("no urls here") == []

    def test_http_url(self):
        urls = extract_urls("http://example.com")
        assert "http://example.com" in urls


class TestComputeUrlOverlap:
    def test_identical_urls(self):
        urls = ["https://a.com", "https://b.com"]
        assert compute_url_overlap(urls, urls) == 1.0

    def test_partial_overlap(self):
        a = ["https://a.com", "https://b.com", "https://c.com"]
        b = ["https://b.com", "https://c.com", "https://d.com"]
        overlap = compute_url_overlap(a, b)
        assert 0.0 < overlap < 1.0

    def test_no_overlap(self):
        assert compute_url_overlap(["https://a.com"], ["https://b.com"]) == 0.0

    def test_empty_lists(self):
        assert compute_url_overlap([], []) == 0.0

    def test_one_empty(self):
        assert compute_url_overlap(["https://a.com"], []) == 0.0
