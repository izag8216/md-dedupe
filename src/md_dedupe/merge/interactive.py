"""Interactive merge UI for reviewing duplicate groups."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from md_dedupe.config import DedupeConfig
from md_dedupe.merge.auto_merge import auto_merge
from md_dedupe.models import DuplicateGroup, ScanResult

TYPE_COLORS = {
    "exact": "green",
    "near": "yellow",
    "url": "blue",
    "frontmatter": "magenta",
}


class InteractiveMerger:
    """Interactive TUI for reviewing and resolving duplicate groups."""

    def __init__(self, result: ScanResult, config: DedupeConfig) -> None:
        self.result = result
        self.config = config
        self.console = Console()
        self.dry_run = True
        self.merged_count = 0
        self.skipped_count = 0
        self.deleted_files: list[Path] = []

    def run(self, apply: bool = False) -> None:
        """Run the interactive merge session.

        Args:
            apply: If True, actually executes merges. If False (default),
                   only shows what would happen (dry-run).
        """
        self.dry_run = not apply

        if not self.result.groups:
            self.console.print("[green]No duplicates found. Nothing to merge.[/green]")
            return

        mode = "[yellow]DRY RUN[/yellow]" if self.dry_run else "[red]LIVE MODE[/red]"
        self.console.print(
            Panel(
                f"Found {len(self.result.groups)} duplicate group(s)\n{mode}",
                title="md-dedupe Interactive Merge",
                border_style="cyan",
            )
        )

        for i, group in enumerate(self.result.groups):
            if not self._review_group(group, i + 1, len(self.result.groups)):
                break

        # Summary
        self.console.print(
            f"\n[bold]Session complete:[/bold] "
            f"{self.merged_count} merged, {self.skipped_count} skipped"
        )
        if self.dry_run and self.merged_count > 0:
            self.console.print(
                "[yellow]This was a dry run. Use --apply to execute changes.[/yellow]"
            )

    def _review_group(self, group: DuplicateGroup, current: int, total: int) -> bool:
        """Review a single group. Returns False if user quits."""
        color = TYPE_COLORS.get(group.duplicate_type, "white")
        sim_str = f"{group.similarity:.0%}" if group.similarity is not None else "N/A"

        # Show group info
        self.console.print(
            Panel(
                f"Type: [{color}]{group.duplicate_type}[/{color}] | Similarity: {sim_str}\n"
                f"Files ({len(group.files)}):",
                title=f"Group {current}/{total} (#{group.group_id})",
                border_style=color,
            )
        )

        # File table
        table = Table(show_lines=True)
        table.add_column("#", width=3)
        table.add_column("Path", min_width=30)
        table.add_column("Size", width=10)
        table.add_column("Frontmatter keys", width=20)

        for i, f in enumerate(group.files):
            fm_keys = ", ".join(sorted(f.frontmatter.keys())) if f.frontmatter else "(none)"
            table.add_row(str(i + 1), str(f.path), f"{f.size} B", fm_keys)

        self.console.print(table)

        # Prompt for action
        self.console.print(
            "\n[bold]Actions:[/bold] "
            "[K]eep all  [M]erge  [S]kip  [Q]uit"
        )

        while True:
            choice = Prompt.ask("Your choice", choices=["k", "m", "s", "q"], default="s")

            if choice == "k":
                self.console.print("[green]Keeping all files.[/green]")
                self.skipped_count += 1
                return True

            if choice == "s":
                self.skipped_count += 1
                return True

            if choice == "q":
                self.console.print("[yellow]Quitting merge session.[/yellow]")
                return False

            if choice == "m":
                rep_idx = self._select_representative(group)
                if rep_idx is None:
                    continue

                self._execute_merge(group, rep_idx)
                return True

        return True

    def _select_representative(self, group: DuplicateGroup) -> int | None:
        """Let user pick the representative file. Returns 0-based index."""
        self.console.print("[bold]Select representative file to keep:[/bold]")
        idx_str = Prompt.ask(
            f"File number (1-{len(group.files)})",
            default="1",
        )
        try:
            idx = int(idx_str) - 1
            if 0 <= idx < len(group.files):
                return idx
            self.console.print("[red]Invalid selection.[/red]")
            return None
        except ValueError:
            self.console.print("[red]Please enter a number.[/red]")
            return None

    def _execute_merge(self, group: DuplicateGroup, rep_idx: int) -> None:
        """Execute or simulate the merge."""
        rep_file = group.files[rep_idx]

        # Update representative
        group.representative = rep_file

        if self.dry_run:
            self.console.print(
                f"[yellow]DRY RUN:[/yellow] Would merge {len(group.files)} files into:\n"
                f"  {rep_file.path}"
            )
            others = [f for f in group.files if f.path != rep_file.path]
            if others:
                self.console.print("[yellow]Would create backups for:[/yellow]")
                for f in others:
                    self.console.print(f"  {f.path} -> {f.path}.bak")
            self.merged_count += 1
        else:
            try:
                result_path = auto_merge(group, backup=True)
                self.console.print(f"[green]Merged into: {result_path}[/green]")
                self.merged_count += 1
            except Exception as e:
                self.console.print(f"[red]Merge failed: {e}[/red]")
