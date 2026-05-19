"""Configuration for Notion MCP Server."""

import os
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DEFAULT_PRIVACY = os.getenv("DEFAULT_PRIVACY", "private").lower()
DEFAULT_PARENT_PAGE_ID = os.getenv("DEFAULT_PARENT_PAGE_ID", "").strip()

if not NOTION_TOKEN:
    raise RuntimeError(
        "❌ NOTION_TOKEN not set. "
        "Get one at https://www.notion.so/my-integrations and add to .env"
    )

NOTION_VERSION = "2022-06-28"