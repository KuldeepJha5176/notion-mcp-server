"""Friendly error handling for Notion API errors."""

import asyncio
from functools import wraps
from typing import Callable


class NotionMCPError(Exception):
    """Base exception for Notion MCP errors."""
    pass


def friendly_error(error: Exception) -> str:
    """Convert technical errors to user-friendly messages."""
    error_str = str(error)
    error_lower = error_str.lower()

    if "object_not_found" in error_lower or "could not find" in error_lower:
        return (
            "❌ Page or database not found. "
            "Make sure it's shared with the integration: "
            "Open the page → ... menu → Connections → Connect to Claude MCP"
        )
    if "unauthorized" in error_lower or "401" in error_str:
        return (
            "❌ Invalid Notion token. "
            "Check NOTION_TOKEN in your .env file."
        )
    if "validation" in error_lower:
        return f"❌ Invalid data: {error_str}"
    if "rate" in error_lower and "limit" in error_lower:
        return "❌ Too many requests. Try again in a moment."
    if "restricted_resource" in error_lower:
        return (
            "❌ Permission denied. Share the page/database with your integration."
        )
    return f"❌ Error: {error_str}"


def with_retry(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator that retries on rate limit errors."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    error_str = str(e).lower()
                    if "rate" in error_str and "limit" in error_str:
                        delay = base_delay * (2 ** attempt)
                        await asyncio.sleep(delay)
                        continue
                    raise
            raise last_error
        return wrapper
    return decorator