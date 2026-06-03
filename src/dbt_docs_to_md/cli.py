from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import toons

from .adapter import build_project, select_layers
from .bundle import build_bundle
from .domain import ParsedProject
from .markdown.environment import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES
from .markdown.index import render_index
from .markdown.inject import inject_summaries
from .markdown.metrics import render_metrics_glossary
from .markdown.renderer import model_relpath, render_model_md


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="dbt-docs-to-md",
        description=(
            "Turn dbt documentation artifacts into a Markdown knowledge base "
            "for business stakeholders."
        ),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Path to manifest.json (required unless --inject)",
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=None,
        help="Path to catalog.json (optional, enriches column data types)",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output directory for generated Markdown",
    )
    parser.add_argument(
        "--no-bundles",
        action="store_true",
        help="Skip writing per-model context bundles (the LLM phase needs them)",
    )
    parser.add_argument(
        "--inject",
        action="store_true",
        help=(
            "Injection mode: splice the prose from <output>/_bundles/**/*.summary.json "
            "into the generated .md files. Run this after writing the summaries; "
            "does not need --manifest."
        ),
    )
    parser.add_argument(
        "--language",
        choices=SUPPORTED_LANGUAGES,
        default=DEFAULT_LANGUAGE,
        help="Language for the generated Markdown (default: %(default)s)",
    )
    parser.add_argument(
        "--layer",
        action="append",
        default=None,
        metavar="LAYER",
        help=(
            "Only document models in this dbt layer (folder), e.g. --layer marts. "
            "Repeat or comma-separate for multiple layers. Reduces output and "
            "LLM token usage by skipping non-business layers."
        ),
    )
    args = parser.parse_args(argv)

    if args.inject:
        if not args.output.is_dir():
            print(f"error: output directory not found: {args.output}", file=sys.stderr)
            return 2
        report = inject_summaries(args.output)
        for warning in report.warnings:
            print(f"warning: {warning}", file=sys.stderr)
        print(
            f"Injected {report.injected} summary(ies) into {args.output} "
            f"(skipped {report.skipped})."
        )
        return 0

    if args.manifest is None:
        parser.error("--manifest is required unless --inject is given")

    layers = [part for value in (args.layer or []) for part in value.split(",")]

    try:
        project = load_project(args.manifest, args.catalog)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(
            f"error: could not parse dbt artifacts: {exc}\n"
            "Ensure manifest.json/catalog.json were produced by `dbt docs generate` "
            "and are a supported schema version (dbt 0.19–1.11).",
            file=sys.stderr,
        )
        return 1

    filtered, available = select_layers(project.models, layers)
    if layers and not filtered:
        print(
            f"warning: no models matched layer(s) {layers}; "
            f"available layers: {', '.join(available) or '(none)'}",
            file=sys.stderr,
        )
    project.models = filtered

    write_outputs(
        project,
        args.output,
        write_bundles=not args.no_bundles,
        language=args.language,
    )
    layer_note = f", layers: {', '.join(layers)}" if layers else ""
    print(
        f"Documented {len(project.models)} model(s) -> {args.output} "
        f"(schema: {project.dbt_schema_version or 'unknown'}{layer_note})."
    )
    return 0


def load_project(manifest_path: Path, catalog_path: Path | None) -> ParsedProject:
    from dbt_artifacts_parser.parser import parse_catalog, parse_manifest

    manifest_obj = parse_manifest(manifest=_read_json(manifest_path))
    catalog_obj = None
    if catalog_path is not None:
        catalog_obj = parse_catalog(catalog=_read_json(catalog_path))
    return build_project(manifest_obj, catalog_obj)


def write_outputs(
    project: ParsedProject,
    output: Path,
    write_bundles: bool = True,
    language: str = DEFAULT_LANGUAGE,
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    filenames = _assign_filenames(project)

    for model in project.models:
        filename = filenames[model.unique_id]
        path = output / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_model_md(model, project, language=language), encoding="utf-8")

    (output / "index.md").write_text(
        render_index(project, filenames, language=language), encoding="utf-8"
    )

    if project.metrics:
        (output / "metrics.md").write_text(
            render_metrics_glossary(project, filenames, language=language),
            encoding="utf-8",
        )

    if write_bundles:
        bundle_dir = output / "_bundles"
        for model in project.models:
            filename = filenames[model.unique_id]
            bundle = build_bundle(model, project, language=language)
            rel = filename[:-3] if filename.endswith(".md") else filename
            bundle_path = bundle_dir / f"{rel}.toon"
            bundle_path.parent.mkdir(parents=True, exist_ok=True)
            bundle_path.write_text(toons.dumps(bundle), encoding="utf-8")


def _assign_filenames(project: ParsedProject) -> dict[str, str]:
    """Assign a unique ``<layer>/<model>.md`` path per model, resolving collisions.

    The path organizes models by dbt layer (warehouse schema) and names the file
    after the technical model name; see :func:`model_relpath`.
    """
    used: set[str] = set()
    result: dict[str, str] = {}
    for model in sorted(project.models, key=lambda m: m.unique_id):
        relpath = model_relpath(model)
        stem = relpath[:-3] if relpath.endswith(".md") else relpath
        candidate = stem
        n = 2
        while candidate in used:
            candidate = f"{stem}-{n}"
            n += 1
        used.add(candidate)
        result[model.unique_id] = f"{candidate}.md"
    return result


def _read_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"file not found: {path}")
    with path.open(encoding="utf-8") as fp:
        return json.load(fp)


if __name__ == "__main__":
    raise SystemExit(main())
