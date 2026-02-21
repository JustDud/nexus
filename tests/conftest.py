"""Shared test fixtures. Sets dummy API keys for the entire test session."""

import os

# Set dummy keys BEFORE any module imports trigger get_settings().
# This must happen at import time of conftest (loaded first by pytest).
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("OPENAI_API_KEY", "test-key")
