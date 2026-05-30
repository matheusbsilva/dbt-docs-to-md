from dbt_docs_to_md.lineage import direct_parents, upstream_tree


def test_direct_parents_are_models(project):
    labels = [p.display_label for p in direct_parents("model.shop.dim_customers", project)]
    assert labels == ["Cleaned Customers", "Cleaned Orders"]


def test_upstream_tree_is_transitive_and_includes_sources(project):
    refs = upstream_tree("model.shop.dim_customers", project)
    labels = {r.display_label for r in refs}
    assert labels == {
        "Cleaned Customers",
        "Cleaned Orders",
        "Source Customers",
        "Source Orders",
    }


def test_upstream_tree_dedup(project):
    refs = upstream_tree("model.shop.dim_customers", project)
    ids = [r.unique_id for r in refs]
    assert len(ids) == len(set(ids))


def test_leaf_model_has_source_parent(project):
    parents = direct_parents("model.shop.stg_customers", project)
    assert [p.resource_type for p in parents] == ["source"]
