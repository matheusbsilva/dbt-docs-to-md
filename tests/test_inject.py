import json

from dbt_docs_to_md.cli import write_outputs
from dbt_docs_to_md.markdown import markers
from dbt_docs_to_md.markdown.inject import inject_summaries, replace_between


def _write_summary(output, rel_stem, lineage=None, transformation=None):
    payload = {}
    if lineage is not None:
        payload["lineage"] = lineage
    if transformation is not None:
        payload["transformation"] = transformation
    path = output / "_bundles" / f"{rel_stem}.summary.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_bundle_is_slim_and_marks_direct(project, tmp_path):
    write_outputs(project, tmp_path)
    bundle = json.loads(
        (tmp_path / "_bundles" / "analytics" / "dim_customers.json").read_text()
    )
    for dropped in ("parents", "placeholders", "target_md", "sql_source"):
        assert dropped not in bundle
    assert bundle["upstream"], "expected upstream entries"
    assert all("direct" in ref for ref in bundle["upstream"])
    directs = {ref["display_label"] for ref in bundle["upstream"] if ref["direct"]}
    assert directs == {"Cleaned Customers", "Cleaned Orders"}


def test_inject_places_prose_between_markers(project, tmp_path):
    write_outputs(project, tmp_path)
    _write_summary(
        tmp_path,
        "analytics/dim_customers",
        lineage="LINEAGE PROSE HERE",
        transformation="TRANSFORM PROSE HERE",
    )

    report = inject_summaries(tmp_path)
    assert report.injected == 1

    md = (tmp_path / "analytics" / "dim_customers.md").read_text()
    assert f"{markers.LINEAGE_OPEN}\nLINEAGE PROSE HERE\n{markers.LINEAGE_CLOSE}" in md
    assert (
        f"{markers.TRANSFORMATION_OPEN}\nTRANSFORM PROSE HERE\n{markers.TRANSFORMATION_CLOSE}"
        in md
    )
    assert "_Pending:" not in md.split("## Columns")[0]


def test_inject_is_idempotent(project, tmp_path):
    write_outputs(project, tmp_path)
    _write_summary(
        tmp_path, "analytics/dim_customers", lineage="A", transformation="B"
    )
    inject_summaries(tmp_path)
    first = (tmp_path / "analytics" / "dim_customers.md").read_text()
    inject_summaries(tmp_path)
    second = (tmp_path / "analytics" / "dim_customers.md").read_text()
    assert first == second


def test_model_without_summary_keeps_placeholder(project, tmp_path):
    write_outputs(project, tmp_path)
    _write_summary(
        tmp_path, "analytics/dim_customers", lineage="X", transformation="Y"
    )
    inject_summaries(tmp_path)
    # stg_customers had no summary written
    md = (tmp_path / "analytics" / "stg_customers.md").read_text()
    assert "_Pending:" in md


def test_missing_marker_is_reported_not_crashing(project, tmp_path):
    write_outputs(project, tmp_path)
    md_path = tmp_path / "analytics" / "dim_customers.md"
    # Strip the lineage markers from the .md
    stripped = md_path.read_text().replace(markers.LINEAGE_OPEN, "").replace(
        markers.LINEAGE_CLOSE, ""
    )
    md_path.write_text(stripped, encoding="utf-8")
    _write_summary(
        tmp_path, "analytics/dim_customers", lineage="X", transformation="Y"
    )

    report = inject_summaries(tmp_path)
    assert report.injected == 0
    assert report.skipped == 1
    assert any("lineage markers" in w for w in report.warnings)


def test_replace_between_returns_false_when_absent():
    text = "no markers here"
    out, ok = replace_between(text, markers.LINEAGE_OPEN, markers.LINEAGE_CLOSE, "x")
    assert ok is False
    assert out == text
