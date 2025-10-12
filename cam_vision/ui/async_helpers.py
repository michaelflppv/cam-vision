"""Helper functions for async operations in Streamlit."""

from __future__ import annotations

import asyncio
from typing import Any, Coroutine


def run_async(coro: Coroutine) -> Any:
    """
    Run async coroutine in Streamlit context.

    Streamlit may have its own event loop, so we need to handle this carefully.

    Args:
        coro: Async coroutine to run

    Returns:
        Result from coroutine
    """
    try:
        # Try to get existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Event loop is running, create a new one for this call
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
        else:
            # Event loop exists but not running, use it
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop exists, create one
        return asyncio.run(coro)
