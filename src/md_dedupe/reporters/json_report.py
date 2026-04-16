"""JSON reporter for scan results."""

from __future__ import annotations

import json
from pathlib import Path

from md_dedupe.models import ScanResult


class JsonReporter:
    """Generate machine-readable JSON report."""

    def report(self, result: ScanResult, output: Path | None = None) -> str:
        """Serialize scan result to JSON.

        Args:
            result: Scan result to serialize.
            output: Optional file path to write JSON. If None, returns string.

        Returns:
            JSON string of the scan result.
        """
        data = result.model_dump(mode="json")

        # Convert Path objects to strings for JSON serialization
        data["path"] = str(data["path"])
        for group in data.get("groups", []):
            for f in group.get("files", []):
                f["path"] = str(f["path"])
            if group.get("representative") and group["representative"].get("path"):
                group["representative"]["path"] = str(group["representative"]["path"])

        json_str = json.dumps(data, indent=2, ensure_ascii=False, default=str)

        if output is not None:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json_str, encoding="utf-8")

        return json_str
