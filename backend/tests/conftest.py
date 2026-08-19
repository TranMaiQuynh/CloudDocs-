"""
Pytest configuration and sys.path setup for test discovery.
Ensures 'app' package is importable and Motor MongoDB event loop is dynamically patched.
"""

import sys
import asyncio
import pytest
from pathlib import Path

# Add root backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database.connection import client as motor_client


@pytest.fixture(autouse=True)
def patch_motor_event_loop():
    """Ensure Motor uses the currently active running event loop for each test."""
    try:
        motor_client.get_io_loop = asyncio.get_running_loop
    except Exception:
        pass
