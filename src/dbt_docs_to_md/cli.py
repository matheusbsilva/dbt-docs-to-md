from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .adapter import build_project
from .bundle import build_bundle
from .domain import ParsedProject
from .markdown.index import render_index
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
    parser.add_argument("--manifest", required=True, type=Path, help="Path to manifest.json")
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
    args = parser.parse_args(argv)

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

    write_outputs(project, args.output, write_bundles=not args.no_bundles)
    print(
        f"Documented {len(project.models)} model(s) -> {args.output} "
        f"(schema: {project.dbt_schema_version or 'unknown'})."
    )
    return 0


def load_project(manifest_path: Path, catalog_path: Path | None) -> ParsedProject:
    from dbt_artifacts_parser.parser import parse_catalog, parse_manifest

    manifest_obj = parse_manifest(manifest=_read_json(manifest_path))
    catalog_obj = None
    if catalog_path is not None:
        catalog_obj = parse_catalog(catalog=_read_json(catalog_path))
    return build_project(manifest_obj, catalog_obj)


def write_outputs(project: ParsedProject, output: Path, write_bundles: bool = True) -> None:
    output.mkdir(parents=True, exist_ok=True)
    filenames = _assign_filenames(project)

    for model in project.models:
        filename = filenames[model.unique_id]
        path = output / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_model_md(model, project), encoding="utf-8")

    (output / "index.md").write_text(render_index(project, filenames), encoding="utf-8")

    if project.metrics:
        (output / "metrics.md").write_text(
            render_metrics_glossary(project, filenames), encoding="utf-8"
        )

    if write_bundles:
        bundle_dir = output / "_bundles"
        for model in project.models:
            filename = filenames[model.unique_id]
            bundle = build_bundle(model, project, target_md=filename)
            rel = filename[:-3] if filename.endswith(".md") else filename
            bundle_path = bundle_dir / f"{rel}.json"
            bundle_path.parent.mkdir(parents=True, exist_ok=True)
            bundle_path.write_text(
                json.dumps(bundle, indent=2, default=str), encoding="utf-8"
            )


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
