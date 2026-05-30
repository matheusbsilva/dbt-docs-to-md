from dbt_docs_to_md.bundle import build_bundle
from dbt_docs_to_md.markdown.metrics import render_metrics_glossary
from dbt_docs_to_md.markdown.renderer import render_model_md


def _model(project, name):
    return next(m for m in project.models if m.name == name)


def test_semantic_model_attached_to_model(project):
    dim = _model(project, "dim_customers")
    assert len(dim.semantic_models) == 1
    sm = dim.semantic_models[0]
    assert sm.display_label == "Customers"
    assert sm.primary_entity == "customer"


def test_entities_dimensions_measures(project):
    sm = _model(project, "dim_customers").semantic_models[0]
    assert [e.display_label for e in sm.entities] == ["Customer"]
    assert {d.display_label for d in sm.dimensions} == {"Customer Status", "Signup Date"}
    measures = {m.display_label: m.agg for m in sm.measures}
    assert measures == {"Lifetime Value": "sum", "Customer Count": "count_distinct"}


def test_dimension_types(project):
    sm = _model(project, "dim_customers").semantic_models[0]
    by_label = {d.display_label: d.type for d in sm.dimensions}
    assert by_label["Customer Status"] == "categorical"
    assert by_label["Signup Date"] == "time"


def test_metrics_resolved_to_model(project):
    dim = _model(project, "dim_customers")
    labels = {m.display_label for m in dim.metrics}
    assert labels == {"Total Lifetime Value", "Customer Count"}


def test_metric_links_to_model_via_semantic_model(project):
    metric = next(m for m in project.metrics if m.name == "total_lifetime_value")
    assert "model.shop.dim_customers" in metric.model_ids
    assert metric.type == "simple"
    assert metric.type_params_summary == "lifetime_value"
    assert metric.meta == {"unit": "USD"}


def test_models_without_semantic_layer_are_empty(project):
    stg = _model(project, "stg_customers")
    assert stg.semantic_models == []
    assert stg.metrics == []


def test_project_level_collections(project):
    assert len(project.semantic_models) == 1
    assert len(project.metrics) == 2


def test_renderer_includes_semantic_sections(project):
    md = render_model_md(_model(project, "dim_customers"), project)
    assert "## Semantic Model" in md
    assert "## Metrics You Can Measure" in md
    assert "Lifetime Value" in md
    assert "**Available metrics:** Total Lifetime Value, Customer Count" in md


def test_renderer_omits_sections_without_semantic_layer(project):
    md = render_model_md(_model(project, "stg_customers"), project)
    assert "## Semantic Model" not in md
    assert "## Metrics You Can Measure" not in md


def test_metrics_glossary(project):
    filenames = {m.unique_id: "f.md" for m in project.models}
    glossary = render_metrics_glossary(project, filenames)
    assert "# Metrics Glossary" in glossary
    assert "Total Lifetime Value" in glossary
    assert "Customer Count" in glossary
    assert "Total metrics: 2" in glossary


def test_bundle_includes_semantic(project):
    dim = _model(project, "dim_customers")
    bundle = build_bundle(dim, project, "customers.md")
    assert bundle["semantic_models"][0]["dimensions"] == ["Customer Status", "Signup Date"]
    assert {m["name"] for m in bundle["metrics"]} == {
        "Total Lifetime Value",
        "Customer Count",
    }
