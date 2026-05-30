import json
from pathlib import Path

import pytest

from dbt_docs_to_md.adapter import build_project

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def manifest_dict():
    return json.loads((FIXTURES / "manifest.json").read_text())


@pytest.fixture(scope="session")
def catalog_dict():
    return json.loads((FIXTURES / "catalog.json").read_text())


@pytest.fixture
def project(manifest_dict, catalog_dict):
    from dbt_artifacts_parser.parser import parse_catalog, parse_manifest

    manifest_obj = parse_manifest(manifest=manifest_dict)
    catalog_obj = parse_catalog(catalog=catalog_dict)
    return build_project(manifest_obj, catalog_obj)
