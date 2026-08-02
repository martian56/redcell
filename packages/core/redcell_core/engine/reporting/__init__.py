"""Session report generation: a humanized narrative rendered into a PDF, plus
JSON and SARIF exports."""

from .generate import generate_report

__all__ = ["generate_report"]
