"""ASGI entry point for the Tidewatch API."""

from .composition.api import create_app

app = create_app()
