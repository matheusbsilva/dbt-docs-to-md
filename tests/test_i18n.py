import pytest

from dbt_docs_to_md.bundle import build_bundle
from dbt_docs_to_md.cli import write_outputs
from dbt_docs_to_md.markdown import markers
from dbt_docs_to_md.markdown.index import render_index
from dbt_docs_to_md.markdown.metrics import render_metrics_glossary
from dbt_docs_to_md.markdown.renderer import render_model_md


def _model(project, name):
    return next(m for m in project.models if m.name == name)


def test_default_language_is_english(project):
    md = render_model_md(_model(project, "dim_customers"), project)
    assert "## Description" in md
    assert "## What This Model Does" in md


def test_pt_br_model_headings(project):
    md = render_model_md(_model(project, "dim_customers"), project, language="pt_BR")
    for heading in [
        "## Descrição",
        "## Contexto de Negócio",
        "## Linhagem de Origem",
        "## O Que Este Modelo Faz",
        "## Colunas",
        "## Modelo Semântico",
        "## Métricas Que Você Pode Medir",
    ]:
        assert heading in md
    assert "**Fontes diretas:** Cleaned Customers, Cleaned Orders" in md


def test_pt_br_keeps_markers(project):
    md = render_model_md(_model(project, "dim_customers"), project, language="pt_BR")
    assert markers.LINEAGE_OPEN in md and markers.LINEAGE_CLOSE in md
    assert markers.TRANSFORMATION_OPEN in md and markers.TRANSFORMATION_CLOSE in md


def test_pt_br_index_and_metrics(project):
    filenames = {m.unique_id: "f.md" for m in project.models}
    index = render_index(project, filenames, language="pt_BR")
    assert "# Índice do Catálogo de Dados" in index
    assert "Total de modelos: 3" in index
    assert "[Ver](f.md)" in index

    glossary = render_metrics_glossary(project, filenames, language="pt_BR")
    assert "# Glossário de Métricas" in glossary
    assert "Total de métricas: 2" in glossary


def test_unsupported_language_raises(project):
    with pytest.raises(ValueError):
        render_model_md(_model(project, "dim_customers"), project, language="fr")


def test_bundle_carries_language(project):
    dim = _model(project, "dim_customers")
    assert build_bundle(dim, project)["language"] == "en"
    assert build_bundle(dim, project, language="pt_BR")["language"] == "pt_BR"


def test_write_outputs_pt_br(project, tmp_path):
    write_outputs(project, tmp_path, language="pt_BR")
    index = (tmp_path / "index.md").read_text(encoding="utf-8")
    assert "Total de modelos: 3" in index
    model_md = (tmp_path / "analytics" / "dim_customers.md").read_text(encoding="utf-8")
    assert "## Descrição" in model_md
