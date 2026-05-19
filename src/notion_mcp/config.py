"""Configuration for Notion MCP Server."""

import os
from dotenv import load_dotenv

load_dotenv()

DEFAULT_PRIVACY = os.getenv("DEFAULT_PRIVACY", "private").lower()
DEFAULT_PARENT_PAGE_ID = os.getenv("DEFAULT_PARENT_PAGE_ID", "").strip()
NOTION_VERSION = "2022-06-28"


def get_notion_token() -> str:
    token = os.getenv("NOTION_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "❌ NOTION_TOKEN not set. "
            "Get one at https://www.notion.so/my-integrations and add to .env"
        )
    return token