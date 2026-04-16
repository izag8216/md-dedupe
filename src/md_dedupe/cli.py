"""CLI interface for md-dedupe."""

from __future__ import annotations

import time
from pathlib import Path

import click
from rich.console import Console

from md_dedupe import __version__
from md_dedupe.config import DedupeConfig
from md_dedupe.core.cluster import merge_groups
from md_dedupe.core.frontmatter_cmp import find_frontmatter_duplicates
from md_dedupe.core.hasher import find_exact_duplicates
from md_dedupe.core.scanner import Scanner
from md_dedupe.core.similarity import find_near_duplicates
from md_dedupe.core.url_extractor import find_url_duplicates
from md_dedupe.models import ScanResult
from md_dedupe.reporters.json_report import JsonReporter
from md_dedupe.reporters.markdown_report import MarkdownReporter
from md_dedupe.reporters.text import TextReporter


@click.group()
@click.version_option(version=__version__)
def main() -> None:
    """md-dedupe -- Find and handle duplicate markdown files."""


@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--threshold", "-t", type=float, default=0.8, help="Similarity threshold (0.0-1.0)")
@click.option("--check-urls", is_flag=True, help="Enable URL-based dedup")
@click.option("--check-frontmatter", is_flag=True, help="Enable frontmatter comparison")
@click.option("--min-size", type=int, default=0, help="Skip files below this size (bytes)")
@click.option("--exclude", multiple=True, help="Additional exclude patterns")
@click.option("--format", "fmt", type=click.Choice(["terminal", "json", "markdown"]), default="terminal")
@click.option("--output", "-o", type=click.Path(), help="Output file path (for json/markdown)")
def scan(
    path: str,
    threshold: float,
    check_urls: bool,
    check_frontmatter: bool,
    min_size: int,
    exclude: tuple[str, ...],
    fmt: str,
    output: str | None,
) -> None:
    """Scan a directory for duplicate markdown files."""
    scan_path = Path(path)

    # Load config, then override with CLI flags
    config = DedupeConfig.find_config(scan_path)
    config.threshold = threshold
    config.check_urls = check_urls
    config.check_frontmatter = check_frontmatter
    config.min_size = min_size
    if exclude:
        config.exclude.extend(exclude)

    console = Console()

    with console.status("[bold green]Scanning markdown files..."):
        start = time.time()
        scanner = Scanner()
        files = scanner.scan(scan_path, config)
        scan_time = time.time() - start

    if not files:
        console.print("[yellow]No markdown files found.[/yellow]")
        return

    console.print(f"Found {len(files)} markdown files. Analyzing duplicates...")

    with console.status("[bold green]Detecting duplicates..."):
        all_groups: list[list] = []

        # Exact dedup (always on)
        exact_groups = find_exact_duplicates(files)
        if exact_groups:
            all_groups.append(exact_groups)

        # Near-duplicate
        near_groups = find_near_duplicates(files, threshold=config.threshold, ngram_size=config.ngram_size)
        if near_groups:
            all_groups.append(near_groups)

        # URL dedup
        if config.check_urls:
            url_groups = find_url_duplicates(files, overlap_threshold=config.url_overlap)
            if url_groups:
                all_groups.append(url_groups)

        # Frontmatter dedup
        if config.check_frontmatter:
            fm_groups = find_frontmatter_duplicates(
                files, fields=config.frontmatter_fields, threshold=config.threshold
            )
            if fm_groups:
                all_groups.append(fm_groups)

        # Merge all detection results
        merged = merge_groups(all_groups)

    result = ScanResult(
        path=scan_path,
        total_files=len(files),
        groups=merged,
        scan_time_seconds=round(scan_time, 2),
        config=config.model_dump(),
    )

    # Report
    if fmt == "terminal":
        reporter = TextReporter(console)
        reporter.report(result)
    elif fmt == "json":
        json_reporter = JsonReporter()
        out_path = Path(output) if output else None
        json_str = json_reporter.report(result, out_path)
        if not out_path:
            console.print(json_str)
    elif fmt == "markdown":
        md_reporter = MarkdownReporter()
        out_path = Path(output) if output else None
        md_str = md_reporter.report(result, out_path)
        if not out_path:
            console.print(md_str)


@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--format", "fmt", type=click.Choice(["terminal", "json", "markdown"]), default="markdown")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
def report(path: str, fmt: str, output: str | None) -> None:
    """Generate a deduplication report."""
    # Report is a scan with specific output format
    scan_path = Path(path)
    config = DedupeConfig.find_config(scan_path)
    config.check_urls = True
    config.check_frontmatter = True

    console = Console()
    scanner = Scanner()

    with console.status("[bold green]Scanning..."):
        start = time.time()
        files = scanner.scan(scan_path, config)

        all_groups: list[list] = []
        exact_groups = find_exact_duplicates(files)
        if exact_groups:
            all_groups.append(exact_groups)
        near_groups = find_near_duplicates(files, threshold=config.threshold)
        if near_groups:
            all_groups.append(near_groups)
        url_groups = find_url_duplicates(files)
        if url_groups:
            all_groups.append(url_groups)
        fm_groups = find_frontmatter_duplicates(files)
        if fm_groups:
            all_groups.append(fm_groups)

        merged = merge_groups(all_groups)
        scan_time = time.time() - start

    result = ScanResult(
        path=scan_path,
        total_files=len(files),
        groups=merged,
        scan_time_seconds=round(scan_time, 2),
        config=config.model_dump(),
    )

    if fmt == "json":
        out_path = Path(output) if output else None
        JsonReporter().report(result, out_path)
        if out_path:
            console.print(f"[green]Report written to {out_path}[/green]")
    elif fmt == "markdown":
        out_path = Path(output) if output else scan_path / "dedup-report.md"
        MarkdownReporter().report(result, out_path)
        console.print(f"[green]Report written to {out_path}[/green]")
    else:
        TextReporter(console).report(result)


@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--interactive", is_flag=True, help="Interactive merge mode")
@click.option("--apply", is_flag=True, help="Actually execute merges (default is dry-run)")
def merge(path: str, interactive: bool, apply: bool) -> None:
    """Merge duplicate markdown files."""
    from md_dedupe.merge.interactive import InteractiveMerger

    scan_path = Path(path)
    config = DedupeConfig.find_config(scan_path)
    config.check_urls = True
    config.check_frontmatter = True

    console = Console()
    scanner = Scanner()

    with console.status("[bold green]Scanning..."):
        start = time.time()
        files = scanner.scan(scan_path, config)

        all_groups: list[list] = []
        exact_groups = find_exact_duplicates(files)
        if exact_groups:
            all_groups.append(exact_groups)
        near_groups = find_near_duplicates(files, threshold=config.threshold)
        if near_groups:
            all_groups.append(near_groups)
        url_groups = find_url_duplicates(files)
        if url_groups:
            all_groups.append(url_groups)
        fm_groups = find_frontmatter_duplicates(files)
        if fm_groups:
            all_groups.append(fm_groups)

        merged = merge_groups(all_groups)
        scan_time = time.time() - start

    result = ScanResult(
        path=scan_path,
        total_files=len(files),
        groups=merged,
        scan_time_seconds=round(scan_time, 2),
        config=config.model_dump(),
    )

    if interactive:
        merger = InteractiveMerger(result, config)
        merger.run(apply=apply)
    else:
        if apply:
            from md_dedupe.merge.auto_merge import auto_merge

            for group in result.groups:
                try:
                    out = auto_merge(group, backup=True)
                    console.print(f"[green]Merged: {out}[/green]")
                except Exception as e:
                    console.print(f"[red]Failed: {e}[/red]")
        else:
            console.print("[yellow]Dry run mode. Use --apply to execute merges.[/yellow]")
            console.print(f"Would merge {len(result.groups)} groups.")
            TextReporter(console).report(result)
