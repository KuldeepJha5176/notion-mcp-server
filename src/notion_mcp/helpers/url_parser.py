"""Parse Notion URLs to extract page/database IDs."""

import re


def extract_id(url_or_id: str) -> str:
    """
    Extract Notion ID from URL or pass-through if already an ID.

    Examples:
        https://www.notion.so/Page-Title-abc123def456...  →  abc123def456...
        https://notion.so/abc123def456...                  →  abc123def456...
        abc123def456...                                     →  abc123def456...
    """
    if not url_or_id:
        raise ValueError("URL or ID cannot be empty")

    if "notion.so" in url_or_id or "notion.site" in url_or_id:
        match = re.search(r"([a-f0-9]{32})", url_or_id.replace("-", ""))
        if not match:
            raise ValueError(f"Could not extract ID from URL: {url_or_id}")
        raw_id = match.group(1)
    else:
        raw_id = url_or_id.replace("-", "")

    if len(raw_id) != 32:
        raise ValueError(f"Invalid Notion ID length: {raw_id}")

    formatted = f"{raw_id[0:8]}-{raw_id[8:12]}-{raw_id[12:16]}-{raw_id[16:20]}-{raw_id[20:32]}"
    return formatted


def get_page_title(page: dict) -> str:
    """Extract title from a page object (handles both pages and database rows)."""
    props = page.get("properties", {})

    for prop_name, prop_data in props.items():
        if prop_data.get("type") == "title":
            title_arr = prop_data.get("title", [])
            if title_arr:
                return "".join(t.get("plain_text", "") for t in title_arr)

    if "title" in page:
        title_arr = page.get("title", [])
        if title_arr:
            return "".join(t.get("plain_text", "") for t in title_arr)

    return "Untitled"