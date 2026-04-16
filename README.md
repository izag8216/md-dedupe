[![header](https://capsule-render.vercel.app/api?type=cylinder&color=0:4A6FA5,100:8BBBD0&fontColor=FDF6E3&height=220&section=header&text=md-dedupe&fontSize=48&fontAlignY=40&desc=Find%20and%20handle%20duplicate%20markdown%20files&descSize=16&descAlignY=55&animation=blinking)](https://github.com/izag8216/md-dedupe)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-78%20passing-green.svg)]()
[![zero API](https://img.shields.io/badge/API-zero%20external-orange.svg)]()

Markdown-based knowledge bases accumulate duplicates over time -- exported notes, clipped articles, bookmark files, research notes. **md-dedupe** detects both exact and near-duplicate markdown files, locally, with zero API dependencies.

[English](#) | [日本語](README.ja.md)

## Installation

```bash
pip install md-dedupe
```

## Quick Start

```bash
# Scan for duplicates
md-dedupe scan /path/to/markdown/files

# Scan with URL and frontmatter detection
md-dedupe scan /path/to/files --check-urls --check-frontmatter

# Adjust similarity threshold
md-dedupe scan /path/to/files --threshold 0.7

# Generate a report
md-dedupe report /path/to/files --format markdown -o report.md

# Interactive merge (dry-run by default)
md-dedupe merge /path/to/files --interactive

# Execute merges
md-dedupe merge /path/to/files --interactive --apply
```

## Features

- **Exact dedup** -- SHA-256 body hashing (frontmatter excluded)
- **Near-duplicate detection** -- n-gram Jaccard similarity with size pre-filter
- **URL-based dedup** -- group files sharing common URLs
- **Frontmatter comparison** -- match on title, date, source fields
- **Union-find clustering** -- merge results from all detection methods
- **Multiple report formats** -- terminal (Rich), JSON, Markdown
- **Interactive merge** -- TUI for reviewing and resolving duplicates
- **Safe defaults** -- dry-run mode, automatic backups before merge
- **Zero API dependencies** -- all computation is local

## Commands

```
md-dedupe scan <path>                          # Find all duplicates
md-dedupe scan <path> --threshold 0.7          # Lower similarity threshold
md-dedupe scan <path> --check-urls             # Include URL-based dedup
md-dedupe scan <path> --check-frontmatter      # Include frontmatter comparison
md-dedupe scan <path> --min-size 100           # Skip files under 100 bytes
md-dedupe scan <path> --format json            # JSON output
md-dedupe report <path> --format markdown      # Generate report file
md-dedupe merge <path> --interactive           # Interactive merge review
md-dedupe merge <path> --apply                 # Execute pending merges
```

## Configuration

Create `.md-dedupe.toml` in your project root:

```toml
threshold = 0.8
ngram_size = 3
check_urls = true
check_frontmatter = true
min_size = 50
url_overlap = 0.8
frontmatter_fields = ["title", "date", "source"]
exclude = [".git", ".obsidian", "node_modules", "__pycache__", ".venv"]
```

## Performance

| Strategy | Complexity | Description |
|----------|-----------|-------------|
| Exact dedup | O(n) | Single SHA-256 pass |
| Size pre-filter | O(n log n) | Only compare pairs within 20% size range |
| URL dedup | O(n) | Build URL-to-file index, then intersect |
| Near-dedup | O(k) | k = candidate pairs after size filter |

Expected: 3000+ files processed in under 30 seconds.

## License

MIT
