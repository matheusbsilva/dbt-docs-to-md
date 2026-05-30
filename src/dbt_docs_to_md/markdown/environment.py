from __future__ import annotations

from functools import lru_cache

from jinja2 import Environment, PackageLoader

from . import markers

DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES = ("en", "pt_BR")


def stringify(value: object) -> str:
    if isinstance(value, (list, tuple)):
        return ", ".join(str(v) for v in value)
    return str(value)


def cell(value: object) -> str:
    """Escape a value for safe inclusion in a Markdown table cell."""
    text = stringify(value)
    text = text.replace("\n", " ").replace("|", "\\|")
    return text.strip()


def inline_meta(meta: dict[str, object]) -> str:
    """Render a meta mapping as a single ``key: value; ...`` line."""
    return "; ".join(f"{k}: {stringify(v)}" for k, v in sorted(meta.items()))


def describe_join(items: list) -> str:
    """Join the ``describe()`` of each test into a comma-separated string."""
    return ", ".join(item.describe() for item in items)


@lru_cache(maxsize=1)
def get_environment() -> Environment:
    """Return the shared Jinja environment that loads the Markdown templates."""
    env = Environment(
        loader=PackageLoader("dbt_docs_to_md.markdown", "templates"),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
        autoescape=False,
    )
    env.filters["cell"] = cell
    env.filters["inline_meta"] = inline_meta
    env.filters["describe_join"] = describe_join
    env.globals.update(
        LINEAGE_OPEN=markers.LINEAGE_OPEN,
        LINEAGE_CLOSE=markers.LINEAGE_CLOSE,
        TRANSFORMATION_OPEN=markers.TRANSFORMATION_OPEN,
        TRANSFORMATION_CLOSE=markers.TRANSFORMATION_CLOSE,
    )
    return env


def render_template(name: str, language: str = DEFAULT_LANGUAGE, **context: object) -> str:
    """Hydrate ``<language>/<name>`` with ``context`` and return the Markdown."""
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"unsupported language {language!r}; choose from {', '.join(SUPPORTED_LANGUAGES)}"
        )
    return get_environment().get_template(f"{language}/{name}").render(**context)
