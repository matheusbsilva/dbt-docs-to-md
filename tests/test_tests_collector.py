def _model(project, name):
    return next(m for m in project.models if m.name == name)


def test_column_tests_attached(project):
    dim = _model(project, "dim_customers")
    by_col = {c.name: c for c in dim.columns}
    names = {t.name for t in by_col["customer_id"].tests}
    assert names == {"not_null", "unique"}


def test_accepted_values_kwargs(project):
    dim = _model(project, "dim_customers")
    status = next(c for c in dim.columns if c.name == "status")
    test = next(t for t in status.tests if t.name == "accepted_values")
    assert test.kwargs["values"] == ["vip", "standard"]
    assert "vip" in test.describe()


def test_relationships_attached_to_column(project):
    orders = _model(project, "stg_orders")
    cust = next(c for c in orders.columns if c.name == "customer_id")
    assert any(t.name == "relationships" for t in cust.tests)


def test_model_level_test(project):
    orders = _model(project, "stg_orders")
    assert any(t.name == "assert_positive_amount" for t in orders.model_tests)


def test_column_name_not_shown_in_describe(project):
    dim = _model(project, "dim_customers")
    cust = next(c for c in dim.columns if c.name == "customer_id")
    not_null = next(t for t in cust.tests if t.name == "not_null")
    # kwargs only carried column_name -> describe() should drop it
    assert not_null.describe() == "not_null"
