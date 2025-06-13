"""
High-level orchestration for the analyser package.
The public surface is `analyse_repo(url) → dict`.
"""
from .main import analyse_repo  # noqa: F401

__all__ = ["analyse_repo"]
