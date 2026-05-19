"""Notion API client wrapper."""

from notion_client import AsyncClient
from .config import NOTION_TOKEN

notion = AsyncClient(auth=NOTION_TOKEN)