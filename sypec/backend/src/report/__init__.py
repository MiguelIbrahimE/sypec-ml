"""
Export build_pdf_report so callers can `from report import build_pdf_report`.
"""
from .tex_builder import build_pdf_report  # noqa: F401

__all__ = ["build_pdf_report"]
