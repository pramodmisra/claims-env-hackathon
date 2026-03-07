"""
HuggingFace Spaces Entry Point

This file is the entry point for HuggingFace Spaces deployment.
Re-exports the app from space_app.py.
"""

# Import directly from space_app which has correct imports
from space_app import app

__all__ = ["app"]
