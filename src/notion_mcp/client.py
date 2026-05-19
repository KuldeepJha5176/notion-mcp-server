"""Notion API client wrapper."""

from functools import lru_cache
from notion_client import AsyncClient
from .config import get_notion_token


@lru_cache(maxsize=1)
def get_notion_client() -> AsyncClient:
    return AsyncClient(auth=get_notion_token())
    