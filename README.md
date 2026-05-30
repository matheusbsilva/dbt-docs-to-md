# dbt-docs-to-md

A Claude Skill that turns **dbt documentation artifacts into a Markdown knowledge
base** — one file per model — designed to power an LLM data catalog and to be read
by **business stakeholders**.

It combines two phases:

1. **A deterministic Python script** parses `manifest.json` (+ optional
   `catalog.json`) and renders the mechanical parts of each model's doc: table and
   column names, descriptions, data types, the tests applied, and all custom
   `meta` keys (model- and column-level).
2. **Claude** (driven by [`SKILL.md`](./SKILL.md)) writes the two prose sections
   that need judgment:
   - an **upstream lineage** summary, naming upstream models/sources by their
     business `label`, and
   - a **transformation** summary inferred from the model's SQL.

## Why a library, not hand-rolled schemas

Parsing and **dbt-schema versioning** are delegated to
[`dbt-artifacts-parser`](https://github.com/yu-iskw/dbt-artifacts-parser), whose
`parse_manifest()` / `parse_catalog()` auto-detect the artifact version
(manifest v1–v12, dbt 0.19–1.11) and return Pydantic v2 objects. A thin
[`adapter`](./src/dbt_docs_to_md/adapter.py) maps those version-specific objects
onto a small, stable [domain model](./src/dbt_docs_to_md/domain.py) so the
renderer never needs to know which dbt version produced the artifacts.

## The `label` meta key

The skill expects a custom `meta.label` on models (and optionally columns) — the
descriptive, business-friendly name. Lineage summaries and the index use `label`
instead of technical model names. When a node has no `label`, the technical name
is used as a fallback.

```yaml
# models/marketing/schema.yml
models:
  - name: dim_customers
    meta:
      label: Customers          # <- business name used in the docs
    columns:
      - name: lifetime_value
        meta:
          label: Lifetime Value
```

## Installation

```bash
pip install -e .          # runtime
pip install -e ".[dev]"   # + pytest
```

Requires Python 3.10+.

## Usage

Generate `manifest.json` and `catalog.json` in your dbt project first
(`dbt docs generate`), then run:

```bash
python -m dbt_docs_to_md \
  --manifest target/manifest.json \
  --catalog  target/catalog.json \
  --output   ./catalog_md \
  --language en          # or pt_BR
```

This writes to `./catalog_md`:

- `index.md` — every model with its description and a link, grouped by layer,
- `<layer>/<model>.md` — one file per model, organized into per-layer folders
  (the model's warehouse schema) and named after the technical model, with
  placeholder regions for the two prose sections,
- `_bundles/<layer>/<model>.json` — compact context bundles (mirroring the model
  tree) used by the LLM phase.

`--catalog` is optional (it enriches column data types). Add `--no-bundles` to
skip the LLM context bundles. `--language` selects the output language (`en` by
default, or `pt_BR` for Brazilian Portuguese); the document structure lives in
per-language Jinja templates under
[`src/dbt_docs_to_md/markdown/templates/<language>/`](./src/dbt_docs_to_md/markdown/templates).

Then run the skill (or follow [`SKILL.md`](./SKILL.md) manually) to fill in the
**Upstream Lineage** and **What This Model Does** sections.

See [`examples/output`](./examples/output) for fully generated sample docs
(including filled-in summaries in `analytics/dim_customers.md`).

## What a model file contains

- Title (business `label`), technical model name, table, tags
- Description
- Business Context — all `meta` keys
- Upstream Lineage — *Claude-authored*, using business labels (+ deterministic
  list of direct sources)
- What This Model Does — *Claude-authored*, from the SQL
- Columns — name, type, description, tests, meta
- Semantic Model — entities, dimensions, measures (when defined)
- Metrics You Can Measure — metrics built on the model (when defined)
- Tests Applied (model level)

## Semantic layer support

When a project uses the **dbt Semantic Layer**, the docs also describe its
semantic models and metrics in business terms:

- each model's file gains **Semantic Model** (entities / dimensions / measures)
  and **Metrics You Can Measure** sections, and
- a top-level **`metrics.md`** glossary lists every metric (label, type, how it's
  calculated, description, and the model it's built on), linked from `index.md`.

This information is read directly from `manifest.json` v12 (which embeds
`semantic_models` and `metrics`). The standalone, dbt Cloud–only
`semantic_manifest.json` artifact is **not** required and is not supported by
`dbt-artifacts-parser` — everything needed is already in `manifest.json`.

## Project layout

```
src/dbt_docs_to_md/
├── cli.py             # CLI entry point (argparse)
├── domain.py          # version-agnostic Pydantic domain models
├── adapter.py         # dbt-artifacts-parser objects -> domain models
├── tests_collector.py # attach dbt test nodes to models/columns
├── semantic_collector.py # collect semantic models + metrics from the manifest
├── lineage.py         # transitive upstream resolution + labels
├── bundle.py          # per-model context bundle for Claude
└── markdown/          # renderer, index, metrics glossary, templates
tests/                 # pytest suite + synthetic v12 fixtures
examples/output/       # sample generated docs
SKILL.md               # Claude Skill manifest + workflow
```

## Development

```bash
python -m pytest
```

Tests run against synthetic v12 fixtures in `tests/fixtures/` (a small shop
project: cleaned customers/orders staging models feeding a `dim_customers`).
