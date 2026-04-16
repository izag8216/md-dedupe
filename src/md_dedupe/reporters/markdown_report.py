"""Markdown reporter for scan results."""

from __future__ import annotations

from pathlib import Path

from md_dedupe.models import ScanResult


class MarkdownReporter:
    """Generate Markdown report file."""

    def report(self, result: ScanResult, output: Path | None = None) -> str:
        """Generate markdown report from scan result.

        Args:
            result: Scan result to report.
            output: Optional file path to write markdown. If None, returns string.

        Returns:
            Markdown string of the report.
        """
        lines: list[str] = [
            "# md-dedupe Report",
            "",
            "## Summary",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Files scanned | {result.total_files} |",
            f"| Duplicate groups | {len(result.groups)} |",
            f"| Files involved | {result.duplicate_file_count} |",
            f"| Est. space savings | {self._format_size(result.space_savings_estimate)} |",
            f"| Scan time | {result.scan_time_seconds:.2f}s |",
            "",
        ]

        if result.groups:
            lines.append("## Duplicate Groups")
            lines.append("")

            for group in result.groups:
                sim_str = f"{group.similarity:.0%}" if group.similarity is not None else "N/A"
                lines.append(f"### Group #{group.group_id} ({group.duplicate_type})")
                lines.append("")
                lines.append(f"**Similarity:** {sim_str}")
                lines.append("")
                lines.append("| File | Size |")
                lines.append("|------|------|")
                for f in group.files:
                    lines.append(f"| `{f.path}` | {self._format_size(f.size)} |")
                lines.append("")

        lines.append("## Recommendations")
        lines.append("")
        if not result.groups:
            lines.append("No duplicates found. Your knowledge base is clean!")
        else:
            lines.append(
                f"Review {len(result.groups)} duplicate group(s) above. "
                "Use `md-dedupe merge <path> --interactive` to resolve them."
            )
        lines.append("")

        md = "\n".join(lines)

        if output is not None:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(md, encoding="utf-8")

        return md

    @staticmethod
    def _format_size(size: int) -> str:
        """Format byte size as human-readable string."""
        if size < 1024:
            return f"{size} B"
        if size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        return f"{size / (1024 * 1024):.1f} MB"
