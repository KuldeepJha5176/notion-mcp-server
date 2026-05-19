"""Notion MCP Server - FastMCP entry point with all tools."""

from typing import Optional, Dict, Any, List
from fastmcp import FastMCP

from .tools.search import search_notion as _search_notion
from .tools.pages import (
    get_page as _get_page,
    create_page as _create_page,
    append_to_page as _append_to_page,
    update_page_title as _update_page_title,
    archive_page as _archive_page,
    restore_page as _restore_page,
)
from .tools.databases import (
    list_databases as _list_databases,
    get_database_schema as _get_database_schema,
    query_database as _query_database,
    add_database_row as _add_database_row,
    update_database_row as _update_database_row,
    bulk_add_rows as _bulk_add_rows,
)
from .tools.blocks import (
    get_block_children as _get_block_children,
    update_block as _update_block,
    delete_block as _delete_block,
    duplicate_page as _duplicate_page,
)
from .tools.comments import (
    add_comment as _add_comment,
    get_comments as _get_comments,
)
from .tools.productivity import (
    quick_note as _quick_note,
    daily_journal as _daily_journal,
    add_task as _add_task,
    get_today_tasks as _get_today_tasks,
    complete_task as _complete_task,
    get_recent_pages as _get_recent_pages,
    learning_dashboard as _learning_dashboard,
)

mcp = FastMCP("notion-mcp")


# ======================================================================
# 🔍 SEARCH & CONNECTION
# ======================================================================

@mcp.tool()
async def search_notion(
    query: str = "",
    filter_type: str = "all",
    limit: int = 20,
) -> dict:
    """Search Notion for pages and databases by keyword."""
    return await _search_notion(query, filter_type, limit)


@mcp.tool()
async def check_connection() -> dict:
    """Verify Notion integration is working."""
    from .client import notion
    response = await notion.search(page_size=1)
    return {
        "status": "✅ Connected" if response else "❌ Failed",
        "accessible_items": "1+" if response.get("results") else "0",
    }


# ======================================================================
# 📄 PAGE OPERATIONS
# ======================================================================

@mcp.tool()
async def get_page(page_id_or_url: str) -> dict:
    """Read a Notion page's full content as markdown."""
    return await _get_page(page_id_or_url)


@mcp.tool()
async def create_page(
    title: str,
    parent_id: str = "",
    content: str = "",
    privacy: str = "private",
) -> dict:
    """Create a new Notion page with markdown content."""
    return await _create_page(title, content, parent_id or None, privacy)


@mcp.tool()
async def append_to_page(page_id_or_url: str, content: str) -> dict:
    """Append markdown content to an existing page."""
    return await _append_to_page(page_id_or_url, content)


@mcp.tool()
async def update_page_title(page_id_or_url: str, new_title: str) -> dict:
    """Rename a Notion page."""
    return await _update_page_title(page_id_or_url, new_title)


@mcp.tool()
async def archive_page(page_id_or_url: str) -> dict:
    """Archive (soft-delete) a Notion page."""
    return await _archive_page(page_id_or_url)


@mcp.tool()
async def restore_page(page_id_or_url: str) -> dict:
    """Restore an archived page."""
    return await _restore_page(page_id_or_url)


@mcp.tool()
async def duplicate_page(page_id_or_url: str, new_title: str = None) -> dict:
    """Duplicate a page (creates a copy with same content)."""
    return await _duplicate_page(page_id_or_url, new_title)


# ======================================================================
# 🗂 DATABASE OPERATIONS
# ======================================================================

@mcp.tool()
async def list_databases() -> dict:
    """List all Notion databases accessible to the integration."""
    return await _list_databases()


@mcp.tool()
async def get_database_schema(database_id_or_url: str) -> dict:
    """
    Get the schema (columns/properties) of a database.
    Use this BEFORE adding/updating rows to know property names and types.
    """
    return await _get_database_schema(database_id_or_url)


@mcp.tool()
async def query_database(
    database_id_or_url: str,
    filters: Optional[Dict[str, Any]] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "descending",
    limit: int = 50,
) -> dict:
    """
    Query a database with filters and sorting.

    Filter examples:
        {"Status": "Learning"}
        {"Priority": "🔥 Critical", "Category": "ML"}
        {"Progress": {"greater_than": 50}}
    """
    return await _query_database(
        database_id_or_url, filters, sort_by, sort_order, limit
    )


@mcp.tool()
async def add_database_row(
    database_id_or_url: str,
    properties: Dict[str, Any],
    content: str = "",
) -> dict:
    """Add a new row to a database."""
    return await _add_database_row(database_id_or_url, properties, content)


@mcp.tool()
async def update_database_row(
    page_id_or_url: str,
    properties: Dict[str, Any],
) -> dict:
    """Update properties of an existing database row."""
    return await _update_database_row(page_id_or_url, properties)


@mcp.tool()
async def bulk_add_rows(
    database_id_or_url: str,
    rows: List[Dict[str, Any]],
) -> dict:
    """Add multiple rows to a database at once."""
    return await _bulk_add_rows(database_id_or_url, rows)


# ======================================================================
# 🧱 BLOCK OPERATIONS
# ======================================================================

@mcp.tool()
async def get_block_children(block_id_or_url: str) -> dict:
    """Get all children blocks of a block (page or container)."""
    return await _get_block_children(block_id_or_url)


@mcp.tool()
async def update_block(block_id_or_url: str, new_content: str) -> dict:
    """Update a single block's text content (for edits)."""
    return await _update_block(block_id_or_url, new_content)


@mcp.tool()
async def delete_block(block_id_or_url: str) -> dict:
    """Delete a single block from a page."""
    return await _delete_block(block_id_or_url)


# ======================================================================
# 💬 COMMENTS
# ======================================================================

@mcp.tool()
async def add_comment(page_id_or_url: str, comment_text: str) -> dict:
    """Add a comment to a Notion page."""
    return await _add_comment(page_id_or_url, comment_text)


@mcp.tool()
async def get_comments(page_id_or_url: str) -> dict:
    """Get all comments on a page."""
    return await _get_comments(page_id_or_url)


# ======================================================================
# ⚡ PRODUCTIVITY SHORTCUTS
# ======================================================================

@mcp.tool()
async def quick_note(content: str, title: Optional[str] = None) -> dict:
    """
    Save a quick note to your default parent page.
    Requires DEFAULT_PARENT_PAGE_ID in .env.
    """
    return await _quick_note(content, title)


@mcp.tool()
async def daily_journal(entry: str, journal_keyword: str = "journal") -> dict:
    """
    Add a timestamped entry to today's journal.
    Auto-finds a page with 'journal' in the title.
    """
    return await _daily_journal(entry, journal_keyword)


@mcp.tool()
async def add_task(
    title: str,
    due_date: Optional[str] = None,
    priority: Optional[str] = None,
    status: str = "Not Started",
    tags: Optional[List[str]] = None,
) -> dict:
    """
    Quick-add a task to your Tasks database (auto-detected).
    Date format: 'YYYY-MM-DD'
    """
    return await _add_task(title, due_date, priority, status, tags)


@mcp.tool()
async def get_today_tasks() -> dict:
    """Get all tasks due today or overdue."""
    return await _get_today_tasks()


@mcp.tool()
async def complete_task(task_name_or_id: str) -> dict:
    """Mark a task as complete by name or ID."""
    return await _complete_task(task_name_or_id)


@mcp.tool()
async def get_recent_pages(limit: int = 10) -> dict:
    """Get recently edited pages."""
    return await _get_recent_pages(limit)


@mcp.tool()
async def learning_dashboard() -> dict:
    """
    Get a dashboard view of your AI/ML learning progress.
    Shows topics by status, category, priority, and average progress.
    """
    return await _learning_dashboard()


# ======================================================================
# ENTRY POINT
# ======================================================================

def main():
    """Entry point for `notion-mcp` command."""
    mcp.run()


if __name__ == "__main__":
    main()