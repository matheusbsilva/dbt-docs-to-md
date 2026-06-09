---
name: dbt-docs-to-md
description: >-
  Convert dbt documentation artifacts (manifest.json + catalog.json) into a
  business-readable Markdown knowledge base — one file per model — for use as an
  LLM data catalog. Use when a user wants to turn dbt docs into Markdown, build an
  LLM/AI catalog from dbt, document dbt models for business stakeholders, or
  summarize dbt model lineage and transformations in plain language.
---

# dbt-docs-to-md

Turn a dbt project's artifacts into Markdown docs aimed at **business
stakeholders** (non-technical readers). A Python script does the deterministic
parsing; you (Claude) write two prose sections per model.

## How it works

1. The script `dbt_docs_to_md` parses `manifest.json` (+ optional `catalog.json`)
   using the `dbt-artifacts-parser` library, which auto-detects the dbt schema
   version (v1–v12). It writes, into the output directory:
   - one `<layer>/<model>.md` per model with all deterministic sections plus two
     placeholder regions. Models are organized by **layer** (their warehouse
     schema, e.g. `analytics/`) and the file is named after the technical model
     (e.g. `analytics/stg_customers.md`).
   - `index.md` listing every model, grouped by layer,
   - `metrics.md` — a business glossary of every metric (only when the project
     uses the dbt Semantic Layer),
   - `_bundles/<layer>/<model>.toon` — a compact context bundle per model
     (mirroring the model tree) that gives you exactly what you need to write the
     prose. It is written in [TOON](https://github.com/toon-format/toon) (a
     token-efficient, human-readable JSON alternative) to minimize read cost. This
     is the **only** file you need to read per model; you do not open the generated
     `.md`.

   When a model has a semantic model / metrics defined on it, the deterministic
   sections **Semantic Model** (entities, dimensions, measures) and **Metrics You
   Can Measure** are already rendered into its `.md` — you do not edit those.
2. You write the two prose sections for each model — **Upstream Lineage** (where
   the data comes from) and **What This Model Does** (the transformations,
   inferred from the SQL) — into a small `*.summary.json` file per model. A second
   run of the script (`--inject`) splices them into the matching `.md`. You never
   open or edit the `.md` files yourself.

## Workflow

1. **Locate artifacts.** Ask the user for `manifest.json` and (optionally)
   `catalog.json` if you don't know the paths. They are usually in the dbt
   project's `target/` directory after running `dbt docs generate`.

2. **Run the parser** (install the package first if needed: `pip install -e .`
   from this skill's directory):

   ```
   python -m dbt_docs_to_md \
     --manifest <path/to/manifest.json> \
     --catalog  <path/to/catalog.json> \
     --output   <output_dir> \
     --language <en|pt_BR>
   ```

   `--language` is optional and defaults to `en`; pass `pt_BR` to generate the
   docs in Brazilian Portuguese. If it errors that the artifacts can't be parsed,
   report the message to the user (likely an unsupported dbt version or a
   non-`docs generate` file) — do not guess or hand-edit the artifacts.

3. **Write the summaries.** For each bundle TOON file (`*.toon`) found recursively
   under `<output_dir>/_bundles/` (they are nested in per-layer subfolders; the
   `*.summary.json` files you write are your output, not inputs):
   a. Read the bundle (TOON). It contains: `description`, the full `upstream` list
      (each with a business `label`/`display_label` and a `direct` flag — `true`
      for immediate sources, `false` for deeper ancestors), the model `sql`,
      `semantic_models` (with dimension and measure labels), `metrics` (label,
      type, description), and `language`. **Write both summaries in the bundle's
      `language`** (`en` → English, `pt_BR` → Brazilian Portuguese) so the prose
      matches the generated document.
   b. Compose an **Upstream Lineage** summary (2–4 sentences). Refer to upstream
      models/sources **only by their `display_label`** (the business name) —
      never the technical model name. Name the immediate sources (`direct: true`)
      first, then trace the origin of the data back through the deeper ancestors.
   c. Compose a **What This Model Does** summary from `sql`: describe the joins,
      aggregations, filters and business logic in plain language (e.g. "combines
      each customer with the total value of their orders and flags high spenders
      as VIP"). Do not paste SQL or use SQL jargon. If the bundle has `metrics`,
      you may add one sentence on what business questions this model helps answer,
      naming the metrics by their label (e.g. "It powers the Total Lifetime Value
      and Customer Count metrics").
   d. **Write** a sibling `<model>.summary.json` next to the bundle, replacing the
      bundle's `.toon` with `.summary.json` (e.g.
      `_bundles/analytics/dim_customers.summary.json`), containing exactly:
      `{"lineage": "<b>", "transformation": "<c>"}`. The summaries stay JSON. Do
      **not** open or edit the `.md` file — the next step does that.

4. **Inject.** Once every summary is written, run the script in injection mode to
   splice the prose into the `.md` files between the markers:

   ```
   python -m dbt_docs_to_md --inject --output <output_dir>
   ```

   It reports how many summaries were injected and skipped. (Re-running step 2's
   generate command overwrites the `.md` files back to placeholders, so always do
   it in the order generate → write summaries → inject. The `*.summary.json` files
   survive a regenerate and can simply be re-injected.)

5. **Report** the number of models documented and the path to `index.md`.

## Writing guidance

- Audience is **non-technical**. Avoid SQL/dbt jargon; explain in business terms.
- Always use the `label` (business name). If an upstream node has no label, the
  bundle falls back to its technical name — use it but keep the prose simple.
- Never invent columns, metrics, or relationships that aren't in the bundle.
- When referencing metrics or dimensions, use their business **label** as shown
  in the bundle.
- Keep each summary concise: a short paragraph each is ideal.
- Write in the bundle's `language`. The document's headings are already in that
  language; keep your prose consistent with it (e.g. Portuguese for `pt_BR`).
