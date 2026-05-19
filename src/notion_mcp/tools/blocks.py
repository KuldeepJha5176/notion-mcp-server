"""Block-level operations for Notion."""

from ..client import get_notion_client
from ..helpers.url_parser import extract_id
from ..helpers.blocks_to_markdown import blocks_to_markdown
from ..helpers.markdown_to_blocks import markdown_to_blocks


async def get_block_children(block_id_or_url: str) -> dict:
    """Get all children blocks of a block (page or container)."""
    notion = get_notion_client()
    block_id = extract_id(block_id_or_url)

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

    blocks_summary = []
    for block in all_blocks:
        blocks_summary.append({
            "id": block["id"],
            "type": block.get("type"),
            "has_children": block.get("has_children", False),
        })

    return {
        "parent_id": block_id,
        "total_blocks": len(all_blocks),
        "blocks": blocks_summary,
        "markdown": blocks_to_markdown(all_blocks),
    }


async def update_block(block_id_or_url: str, new_content: str) -> dict:
    """Update a single block's text content."""
    notion = get_notion_client()
    block_id = extract_id(block_id_or_url)

    block = await notion.blocks.retrieve(block_id=block_id)
    block_type = block.get("type")

    valid_types = (
        "paragraph", "heading_1", "heading_2", "heading_3",
        "bulleted_list_item", "numbered_list_item", "to_do",
        "quote", "callout", "code"
    )
    if block_type not in valid_types:
        raise ValueError(f"Cannot update block of type '{block_type}'")

    new_blocks = markdown_to_blocks(new_content)
    if not new_blocks:
        raise ValueError("New content is empty")

    new_rich_text = new_blocks[0].get(new_blocks[0]["type"], {}).get("rich_text", [])

    update_data = {block_type: {"rich_text": new_rich_text}}

    if block_type == "to_do":
        update_data["to_do"]["checked"] = block.get("to_do", {}).get("checked", False)

    await notion.blocks.update(block_id=block_id, **update_data)

    return {
        "success": True,
        "block_id": block_id,
        "block_type": block_type,
        "message": "✅ Block updated",
    }


async def delete_block(block_id_or_url: str) -> dict:
    """Delete a single block."""
    notion = get_notion_client()
    block_id = extract_id(block_id_or_url)
    await notion.blocks.delete(block_id=block_id)
    return {
        "success": True,
        "block_id": block_id,
        "message": "🗑 Block deleted",
    }


async def duplicate_page(page_id_or_url: str, new_title: str = None) -> dict:
    """Duplicate a page (creates a copy with same content)."""
    notion = get_notion_client()
    page_id = extract_id(page_id_or_url)

    # Get original page
    original = await notion.pages.retrieve(page_id=page_id)
    parent = original.get("parent", {})

    # Get all blocks from original
    all_blocks = []
    cursor = None
    while True:
        kwargs = {"block_id": page_id, "page_size": 100}
        if cursor:
            kwargs["start_cursor"] = cursor
        response = await notion.blocks.children.list(**kwargs)
        all_blocks.extend(response.get("results", []))
        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")

    # Strip block IDs (so they're created fresh)
    def clean_block(block):
        block_type = block.get("type")
        if not block_type:
            return None
        return {
            "object": "block",
            "type": block_type,
            block_type: block.get(block_type, {}),
        }

    clean_blocks = [b for b in (clean_block(b) for b in all_blocks) if b]

    # Get title
    from ..helpers.url_parser import get_page_title
    original_title = get_page_title(original)
    title = new_title or f"{original_title} (Copy)"

    # Determine parent type for new page
    if parent.get("type") == "database_id":
        new_parent = {"database_id": parent["database_id"]}
        properties = {}
        from ..helpers.property_builder import build_properties
        db = await notion.databases.retrieve(database_id=parent["database_id"])
        title_prop = next(
            (k for k, v in db["properties"].items() if v["type"] == "title"),
            "Name"
        )
        properties[title_prop] = {
            "title": [{"type": "text", "text": {"content": title}}]
        }
    else:
        new_parent = {"page_id": parent.get("page_id", parent.get("workspace"))}
        properties = {
            "title": [{"type": "text", "text": {"content": title}}]
        }

    new_page = await notion.pages.create(
        parent=new_parent,
        properties=properties,
        children=clean_blocks[:100],
    )

    # Append remaining blocks
    if len(clean_blocks) > 100:
        for i in range(100, len(clean_blocks), 100):
            await notion.blocks.children.append(
                block_id=new_page["id"],
                children=clean_blocks[i:i+100],
            )

    return {
        "success": True,
        "id": new_page["id"],
        "url": new_page["url"],
        "title": title,
        "blocks_copied": len(clean_blocks),
        "message": f"📄 Page duplicated as '{title}'",
    }
