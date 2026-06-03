from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import markers

SUMMARY_SUFFIX = ".summary.json"


@dataclass
class InjectReport:
    injected: int = 0
    skipped: int = 0
    warnings: list[str] = field(default_factory=list)


def replace_between(
    text: str, open_marker: str, close_marker: str, replacement: str
) -> tuple[str, bool]:
    """Replace the content between two markers, keeping the markers themselves.

    Returns ``(new_text, replaced)``. ``replaced`` is ``False`` (and the text is
    returned unchanged) when the marker pair is not found.
    """
    pattern = re.compile(
        re.escape(open_marker) + r".*?" + re.escape(close_marker),
        re.DOTALL,
    )
    new_block = f"{open_marker}\n{replacement.strip()}\n{close_marker}"
    # Use a callable replacement so backslashes / group refs in the prose are literal.
    new_text, count = pattern.subn(lambda match: new_block, text, count=1)
    return new_text, bool(count)


def inject_summaries(output: Path) -> InjectReport:
    """Splice Claude-written ``*.summary.json`` prose into the generated ``.md`` files.

    Walks ``output/_bundles`` for ``<model>.summary.json`` files and, for each,
    replaces the lineage and transformation placeholder regions of the matching
    ``<model>.md`` (located by mirroring the bundle's relative path under the
    output root).
    """
    report = InjectReport()
    bundle_dir = output / "_bundles"
    if not bundle_dir.is_dir():
        report.warnings.append(f"no _bundles directory under {output}")
        return report

    for summary_path in sorted(bundle_dir.rglob(f"*{SUMMARY_SUFFIX}")):
        rel = summary_path.relative_to(bundle_dir)
        stem = str(rel)[: -len(SUMMARY_SUFFIX)]
        md_path = output / f"{stem}.md"

        if not md_path.exists():
            report.skipped += 1
            report.warnings.append(f"no target .md for {rel} (expected {stem}.md)")
            continue

        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            report.skipped += 1
            report.warnings.append(f"could not read {rel}: {exc}")
            continue

        text = md_path.read_text(encoding="utf-8")
        lineage = summary.get("lineage")
        transformation = summary.get("transformation")
        missing: list[str] = []

        if lineage:
            text, ok = replace_between(
                text, markers.LINEAGE_OPEN, markers.LINEAGE_CLOSE, lineage
            )
            if not ok:
                missing.append("lineage markers")
        if transformation:
            text, ok = replace_between(
                text,
                markers.TRANSFORMATION_OPEN,
                markers.TRANSFORMATION_CLOSE,
                transformation,
            )
            if not ok:
                missing.append("transformation markers")

        if missing:
            report.skipped += 1
            report.warnings.append(f"{stem}.md: {', '.join(missing)} not found")
            continue

        md_path.write_text(text, encoding="utf-8")
        report.injected += 1

    return report
