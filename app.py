"""
HuggingFace Spaces Entry Point

This file is the entry point for HuggingFace Spaces deployment.
It re-exports the app from server/app.py.
"""

from claims_env.server.app import app

# This is what HF Spaces will run
__all__ = ["app"]
