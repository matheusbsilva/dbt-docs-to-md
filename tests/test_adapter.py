def _model(project, name):
    return next(m for m in project.models if m.name == name)


def test_models_extracted(project):
    names = {m.name for m in project.models}
    assert names == {"stg_customers", "stg_orders", "dim_customers"}


def test_schema_version_detected(project):
    assert "v12" in project.dbt_schema_version


def test_label_resolved_from_meta(project):
    assert _model(project, "dim_customers").label == "Customers"
    assert _model(project, "dim_customers").display_label == "Customers"


def test_meta_merged_and_complete(project):
    meta = _model(project, "dim_customers").meta
    assert meta["label"] == "Customers"
    assert meta["owner"] == "analytics-team"
    assert meta["domain"] == "marketing"


def test_columns_and_descriptions(project):
    dim = _model(project, "dim_customers")
    cols = {c.name: c for c in dim.columns}
    assert cols["customer_id"].description == "Unique identifier of the customer."
    assert cols["email"].meta == {"pii": True}


def test_data_type_enriched(project):
    # declared data_type on the column is preserved
    dim = _model(project, "dim_customers")
    assert {c.name: c.data_type for c in dim.columns}["status"] == "varchar"


def test_parents_recorded(project):
    dim = _model(project, "dim_customers")
    assert set(dim.parents) == {"model.shop.stg_customers", "model.shop.stg_orders"}


def test_sources_referenceable(project):
    assert "source.shop.raw.customers" in project.nodes_by_id
    assert project.nodes_by_id["source.shop.raw.customers"].label == "Source Customers"


def test_compiled_sql_preferred(project):
    dim = _model(project, "dim_customers")
    assert dim.transformation_sql == dim.compiled_code
    assert "warehouse" in dim.transformation_sql
