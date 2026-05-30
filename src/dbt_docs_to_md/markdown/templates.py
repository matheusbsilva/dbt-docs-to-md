"""Shared Markdown constants: placeholder markers for the LLM-authored sections.

The deterministic renderer writes everything except two prose sections. Those
sections are bracketed by HTML-comment markers so Claude (driven by SKILL.md) can
locate and replace exactly that region without disturbing the rest of the file.
"""

LINEAGE_OPEN = "<!-- LINEAGE_SUMMARY -->"
LINEAGE_CLOSE = "<!-- /LINEAGE_SUMMARY -->"
TRANSFORMATION_OPEN = "<!-- TRANSFORMATION_SUMMARY -->"
TRANSFORMATION_CLOSE = "<!-- /TRANSFORMATION_SUMMARY -->"

LINEAGE_PLACEHOLDER = "_Pending: lineage summary to be written from the model's upstream sources._"
TRANSFORMATION_PLACEHOLDER = "_Pending: transformation summary to be written from the model's SQL._"
