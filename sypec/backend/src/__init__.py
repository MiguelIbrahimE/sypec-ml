"""
Make backend.src a proper Python package.
Exposes top-level helpers if you ever want `from backend import analyse_repo`.
"""
from .api import app  # FastAPI application instance

__all__ = ["app"]
