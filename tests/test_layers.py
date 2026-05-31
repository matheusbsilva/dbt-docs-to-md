"""Tests for the ``--layer`` filter: fqn-based layer selection of models."""

from dbt_docs_to_md.adapter import select_layers


def _names(models):
    return {m.name for m in models}


def test_fqn_and_layers_populated(project):
    by_name = {m.name: m for m in project.models}
    assert by_name["dim_customers"].fqn == ["shop", "marts", "dim_customers"]
    assert by_name["dim_customers"].layers == ["marts"]
    assert by_name["stg_customers"].layers == ["staging"]


def test_available_layers_listed(project):
    _, available = select_layers(project.models, None)
    assert available == ["marts", "staging"]


def test_no_layers_returns_all(project):
    filtered, _ = select_layers(project.models, None)
    assert _names(filtered) == {"stg_customers", "stg_orders", "dim_customers"}


def test_filter_single_layer(project):
    filtered, _ = select_layers(project.models, ["marts"])
    assert _names(filtered) == {"dim_customers"}


def test_filter_is_case_insensitive(project):
    filtered, _ = select_layers(project.models, ["MARTS"])
    assert _names(filtered) == {"dim_customers"}


def test_filter_multiple_layers(project):
    filtered, _ = select_layers(project.models, ["staging"])
    assert _names(filtered) == {"stg_customers", "stg_orders"}


def test_unknown_layer_yields_empty(project):
    filtered, available = select_layers(project.models, ["nope"])
    assert filtered == []
    assert available == ["marts", "staging"]
