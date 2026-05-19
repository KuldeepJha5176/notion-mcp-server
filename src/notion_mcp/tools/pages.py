"""Page CRUD operations for Notion."""

from typing import Optional
from ..client import notion
from ..helpers.url_parser import extract_id, get_page_title
from ..helpers.markdown_to_blocks import markdown_to_blocks
from ..helpers.blocks_to_markdown import blocks_to_markdown
from ..config import DEFAULT_PRIVACY


# ----------------------------------------------------------------------
# Helper: Recursively fetch all blocks (handles pagination + nesting)
# ----------------------------------------------------------------------

async def fetch_all_blocks(block_id: str) -> list[dict]:
    """Fetch all child blocks of a page/block, handling pagination."""
    all_blocks = []
    cursor = None

    while True:
        kwargs = {"block_id": block_id, "page_size": 100}
        if cursor:
            kwargs["start_cursor"] = cursor

        response = await notion.blocks.children.list(**kwargs)
        all_blocks.extend(response.get("results", []))

        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")

    return all_blocks


# ----------------------------------------------------------------------
# Tool: Get Page Content
# ----------------------------------------------------------------------

async def get_page(page_id_or_url: str) -> dict:
    """Fetch a Notion page including its full content as markdown."""
    page_id = extract_id(page_id_or_url)

    # Get page metadata
    page = await notion.pages.retrieve(page_id=page_id)
    title = get_page_title(page)

    # Get page content blocks
    blocks = await fetch_all_blocks(page_id)
    markdown = blocks_to_markdown(blocks)

    # Extract properties (for database rows)
    properties = {}
    for prop_name, prop_data in page.get("properties", {}).items():
        prop_type = prop_data.get("type")
        if prop_type == "title":
            continue  # already in title
        properties[prop_name] = _format_property_value(prop_data)

    return {
        "id": page["id"],
        "title": title,
        "url": page["url"],
        "created": page["created_time"],
        "last_edited": page["last_edited_time"],
        "archived": page.get("archived", False),
        "properties": properties,
        "content_markdown": markdown,
        "block_count": len(blocks),
    }


def _format_property_value(prop: dict) -> any:
    """Format a Notion property value to a readable form."""
    ptype = prop.get("type")
    val = prop.get(ptype)

    if val is None:
        return None
    if ptype == "rich_text":
        return "".join(t.get("plain_text", "") for t in val)
    if ptype == "number":
        return val
    if ptype == "select":
        return val.get("name") if val else None
    if ptype == "multi_select":
        return [s.get("name") for s in val]
    if ptype == "date":
        return val.get("start") if val else None
    if ptype == "checkbox":
        return val
    if ptype == "url":
        return val
    if ptype == "email":
        return val
    if ptype == "phone_number":
        return val
    if ptype == "people":
        return [p.get("name", "Unknown") for p in val]
    if ptype == "status":
        return val.get("name") if val else None
    return str(val)


# ----------------------------------------------------------------------
# Tool: Create Page
# ----------------------------------------------------------------------
async def create_page(
    title: str,
    content: str = "",
    parent_id: Optional[str] = None,
    privacy: str = None,
) -> dict:
    """
    Create a new Notion page with optional markdown content.

    Args:
        title: Page title
        content: Markdown content (optional)
        parent_id: Parent page/database ID, URL, or "workspace" for top-level
                   If None, uses DEFAULT_PARENT_PAGE_ID from .env
        privacy: 'private' or 'public' (default from config)
    """
    from ..config import DEFAULT_PARENT_PAGE_ID

    privacy = (privacy or DEFAULT_PRIVACY).lower()

    # ----- Resolve parent -----
    is_workspace = False
    parent: dict = {}

    # Case 1: Explicit "workspace" keyword
    if parent_id and str(parent_id).lower() in ("workspace", "root", "top"):
        parent = {"type": "workspace", "workspace": True}
        is_workspace = True

    # Case 2: No parent_id provided, fall back to default
    elif not parent_id:
        if DEFAULT_PARENT_PAGE_ID:
            try:
                resolved_id = extract_id(DEFAULT_PARENT_PAGE_ID)
                parent = {"page_id": resolved_id}
            except Exception:
                raise ValueError(
                    "No parent_id provided and DEFAULT_PARENT_PAGE_ID is invalid. "
                    "Either provide parent_id, set DEFAULT_PARENT_PAGE_ID in .env, "
                    "or use parent_id='workspace' for top-level."
                )
        else:
            raise ValueError(
                "parent_id is required. Options:\n"
                "  • Pass a page/database ID or URL\n"
                "  • Pass 'workspace' to create at top level (requires permissions)\n"
                "  • Set DEFAULT_PARENT_PAGE_ID in .env"
            )

    # Case 3: Specific page/database ID provided
    else:
        parent_id = extract_id(parent_id)
        try:
            await notion.pages.retrieve(page_id=parent_id)
            parent = {"page_id": parent_id}
        except Exception:
            try:
                await notion.databases.retrieve(database_id=parent_id)
                parent = {"database_id": parent_id}
            except Exception as e:
                raise ValueError(
                    f"Parent ID is neither a page nor database: {parent_id}. "
                    f"Make sure it's shared with the integration. Error: {e}"
                )

    # ----- Build properties -----
    is_database = parent.get("database_id") is not None

    if is_database:
        db = await notion.databases.retrieve(database_id=parent["database_id"])
        title_prop_name = next(
            (k for k, v in db["properties"].items() if v["type"] == "title"),
            "Name",
        )
        properties = {
            title_prop_name: {
                "title": [{"type": "text", "text": {"content": title}}]
            }
        }
    else:
        properties = {
            "title": [{"type": "text", "text": {"content": title}}]
        }

    # ----- Convert markdown to blocks -----
    children = markdown_to_blocks(content) if content else []
    initial_children = children[:100]
    remaining_children = children[100:]

    # ----- Create the page (with friendly error for workspace fail) -----
    try:
        new_page = await notion.pages.create(
            parent=parent,
            properties=properties,
            children=initial_children,
        )
    except Exception as e:
        if is_workspace:
            raise ValueError(
                "❌ Cannot create workspace-level page.\n\n"
                "Internal Notion integrations cannot create pages at the workspace root. "
                "This is a Notion API limitation, not an MCP issue.\n\n"
                "Solutions:\n"
                "  1. Create the page under an existing top-level page instead\n"
                "  2. Set DEFAULT_PARENT_PAGE_ID in .env to your preferred parent\n"
                "  3. Manually create one parent page in Notion, share it with the integration, "
                "and use it as parent_id\n\n"
                f"Original error: {e}"
            )
        raise

    # Append remaining blocks if content was huge
    if remaining_children:
        for i in range(0, len(remaining_children), 100):
            batch = remaining_children[i:i + 100]
            await notion.blocks.children.append(
                block_id=new_page["id"],
                children=batch,
            )

    return {
        "success": True,
        "id": new_page["id"],
        "title": title,
        "url": new_page["url"],
        "privacy": privacy,
        "parent_type": "workspace" if is_workspace
                       else ("database" if is_database else "page"),
        "blocks_created": len(children),
        "message": f"✅ Page '{title}' created ({privacy})",
    }

# ----------------------------------------------------------------------
# Tool: Append to Page
# ----------------------------------------------------------------------

async def append_to_page(page_id_or_url: str, content: str) -> dict:
    """Append markdown content as new blocks to an existing page."""
    page_id = extract_id(page_id_or_url)
    blocks = markdown_to_blocks(content)

    if not blocks:
        return {"success": False, "message": "No content to append"}

    # Append in batches of 100
    for i in range(0, len(blocks), 100):
        batch = blocks[i:i + 100]
        await notion.blocks.children.append(block_id=page_id, children=batch)

    return {
        "success": True,
        "page_id": page_id,
        "blocks_appended": len(blocks),
        "message": f"✅ Appended {len(blocks)} blocks to page",
    }


# ----------------------------------------------------------------------
# Tool: Update Page Title
# ----------------------------------------------------------------------

async def update_page_title(page_id_or_url: str, new_title: str) -> dict:
    """Rename a Notion page."""
    page_id = extract_id(page_id_or_url)

    # Get the page to find the title property
    page = await notion.pages.retrieve(page_id=page_id)

    title_prop_name = next(
        (k for k, v in page.get("properties", {}).items() if v.get("type") == "title"),
        "title",
    )

    await notion.pages.update(
        page_id=page_id,
        properties={
            title_prop_name: {
                "title": [{"type": "text", "text": {"content": new_title}}]
            }
        },
    )

    return {
        "success": True,
        "page_id": page_id,
        "new_title": new_title,
        "message": f"✅ Page renamed to '{new_title}'",
    }


# ----------------------------------------------------------------------
# Tool: Archive Page (soft delete)
# ----------------------------------------------------------------------

async def archive_page(page_id_or_url: str) -> dict:
    """Archive (soft-delete) a Notion page. Recoverable from Trash."""
    page_id = extract_id(page_id_or_url)

    await notion.pages.update(page_id=page_id, archived=True)

    return {
        "success": True,
        "page_id": page_id,
        "message": "🗑 Page archived (recoverable from Notion Trash)",
    }


# ----------------------------------------------------------------------
# Tool: Restore Archived Page
# ----------------------------------------------------------------------

async def restore_page(page_id_or_url: str) -> dict:
    """Restore an archived page."""
    page_id = extract_id(page_id_or_url)

    await notion.pages.update(page_id=page_id, archived=False)

    return {
        "success": True,
        "page_id": page_id,
        "message": "♻️ Page restored from archive",
    }