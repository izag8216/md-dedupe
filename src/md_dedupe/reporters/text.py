"""Rich terminal reporter for scan results."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from md_dedupe.models import ScanResult

TYPE_COLORS = {
    "exact": "green",
    "near": "yellow",
    "url": "blue",
    "frontmatter": "magenta",
}


class TextReporter:
    """Display scan results as formatted terminal output."""

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()

    def report(self, result: ScanResult) -> None:
        """Print formatted scan report to terminal."""
        self._print_summary(result)
        if result.groups:
            self._print_groups(result)

    def _print_summary(self, result: ScanResult) -> None:
        """Print summary statistics."""
        total_dupes = result.duplicate_file_count
        savings = result.space_savings_estimate

        summary = (
            f"[bold]Files scanned:[/bold] {result.total_files}\n"
            f"[bold]Duplicate groups:[/bold] {len(result.groups)}\n"
            f"[bold]Files involved:[/bold] {total_dupes}\n"
            f"[bold]Est. space savings:[/bold] {self._format_size(savings)}\n"
            f"[bold]Scan time:[/bold] {result.scan_time_seconds:.2f}s"
        )
        self.console.print(Panel(summary, title="md-dedupe Scan Results", border_style="cyan"))

    def _print_groups(self, result: ScanResult) -> None:
        """Print duplicate group details."""
        table = Table(title="Duplicate Groups", show_lines=True)
        table.add_column("Group", style="bold", width=6)
        table.add_column("Type", width=12)
        table.add_column("Similarity", width=10)
        table.add_column("Files", min_width=40)
        table.add_column("Size", width=10)

        for group in result.groups:
            color = TYPE_COLORS.get(group.duplicate_type, "white")
            sim_str = f"{group.similarity:.2%}" if group.similarity is not None else "N/A"
            file_list = "\n".join(str(f.path) for f in group.files)
            sizes = "\n".join(self._format_size(f.size) for f in group.files)

            table.add_row(
                f"#{group.group_id}",
                f"[{color}]{group.duplicate_type}[/{color}]",
                sim_str,
                file_list,
                sizes,
            )

        self.console.print(table)

    @staticmethod
    def _format_size(size: int) -> str:
        """Format byte size as human-readable string."""
        if size < 1024:
            return f"{size} B"
        if size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        return f"{size / (1024 * 1024):.1f} MB"
