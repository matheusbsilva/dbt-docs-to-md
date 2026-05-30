from dbt_docs_to_md.cli import write_outputs
from dbt_docs_to_md.markdown import templates
from dbt_docs_to_md.markdown.index import render_index
from dbt_docs_to_md.markdown.renderer import model_relpath, render_model_md


def _model(project, name):
    return next(m for m in project.models if m.name == name)


def test_render_contains_sections(project):
    md = render_model_md(_model(project, "dim_customers"), project)
    for heading in [
        "# Customers",
        "## Description",
        "## Business Context",
        "## Upstream Lineage",
        "## What This Model Does",
        "## Columns",
    ]:
        assert heading in md


def test_placeholders_present(project):
    md = render_model_md(_model(project, "dim_customers"), project)
    assert templates.LINEAGE_OPEN in md and templates.LINEAGE_CLOSE in md
    assert templates.TRANSFORMATION_OPEN in md and templates.TRANSFORMATION_CLOSE in md


def test_direct_sources_use_labels(project):
    md = render_model_md(_model(project, "dim_customers"), project)
    assert "**Direct sources:** Cleaned Customers, Cleaned Orders" in md


def test_column_table_has_tests(project):
    md = render_model_md(_model(project, "dim_customers"), project)
    assert "not_null, unique" in md
    assert "accepted_values (values: vip, standard)" in md


def test_model_relpath_uses_schema_and_name(project):
    assert model_relpath(_model(project, "dim_customers")) == "analytics/dim_customers.md"


def test_index_lists_all_models(project):
    filenames = {m.unique_id: model_relpath(m) for m in project.models}
    index = render_index(project, filenames)
    assert "Customers (`dim_customers`)" in index
    assert "Total models: 3" in index
    assert "## analytics" in index


def test_pipe_escaping_in_cells(project):
    model = _model(project, "dim_customers")
    # column descriptions are rendered inside a Markdown table, so pipes must be escaped
    model.columns[0].description = "has a | pipe"
    md = render_model_md(model, project)
    assert "has a \\| pipe" in md


def test_write_outputs_creates_files(project, tmp_path):
    write_outputs(project, tmp_path)
    assert (tmp_path / "index.md").exists()
    assert (tmp_path / "analytics" / "dim_customers.md").exists()
    bundles = list((tmp_path / "_bundles").rglob("*.json"))
    assert len(bundles) == 3
    assert (tmp_path / "_bundles" / "analytics" / "dim_customers.json").exists()
