"""Database CRUD operations for Notion."""

from typing import Optional, List, Dict, Any
from ..client import get_notion_client
from ..helpers.url_parser import extract_id, get_page_title
from ..helpers.property_builder import (
    build_properties,
    build_filter,
    parse_property_value,
)
from ..helpers.cache import schema_cache


async def _get_schema(db_id: str) -> dict:
    """Get database schema with caching."""
    cached = schema_cache.get(db_id)
    if cached:
        return cached

    notion = get_notion_client()
    db = await notion.databases.retrieve(database_id=db_id)
    schema = {
        name: {"type": data.get("type"), "raw": data}
        for name, data in db.get("properties", {}).items()
    }
    schema_cache.set(db_id, schema)
    return schema


async def list_databases() -> dict:
    """List all databases accessible to the integration."""
    notion = get_notion_client()
    response = await notion.search(
        filter={"property": "object", "value": "database"},
        page_size=100,
    )

    databases = []
    for db in response.get("results", []):
        title_arr = db.get("title", [])
        title = "".join(t.get("plain_text", "") for t in title_arr) or "Untitled"

        databases.append({
            "id": db["id"],
            "title": title,
            "url": db["url"],
            "created": db.get("created_time"),
            "last_edited": db.get("last_edited_time"),
            "property_count": len(db.get("properties", {})),
        })

    return {"total": len(databases), "databases": databases}


async def get_database_schema(database_id_or_url: str) -> dict:
    """Get the full schema (columns/properties) of a database."""
    notion = get_notion_client()
    db_id = extract_id(database_id_or_url)
    db = await notion.databases.retrieve(database_id=db_id)

    title_arr = db.get("title", [])
    title = "".join(t.get("plain_text", "") for t in title_arr) or "Untitled"

    properties = {}
    for prop_name, prop_data in db.get("properties", {}).items():
        ptype = prop_data.get("type")
        info = {"type": ptype}

        if ptype in ("select", "multi_select"):
            options = prop_data.get(ptype, {}).get("options", [])
            info["options"] = [opt.get("name") for opt in options]
        elif ptype == "status":
            options = prop_data.get("status", {}).get("options", [])
            info["options"] = [opt.get("name") for opt in options]
            groups = prop_data.get("status", {}).get("groups", [])
            info["groups"] = [g.get("name") for g in groups]
        elif ptype == "number":
            fmt = prop_data.get("number", {}).get("format", "number")
            info["format"] = fmt

        properties[prop_name] = info

    return {
        "id": db["id"],
        "title": title,
        "url": db["url"],
        "properties": properties,
        "property_names": list(properties.keys()),
    }


async def query_database(
    database_id_or_url: str,
    filters: Optional[Dict[str, Any]] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "descending",
    limit: int = 50,
) -> dict:
    """Query a database with filters and sorting."""
    notion = get_notion_client()
    db_id = extract_id(database_id_or_url)
    schema = await _get_schema(db_id)

    params: Dict[str, Any] = {
        "database_id": db_id,
        "page_size": min(limit, 100),
    }

    if filters:
        filter_obj = build_filter(filters, schema)
        if filter_obj:
            params["filter"] = filter_obj

    if sort_by and sort_by in schema:
        params["sorts"] = [{"property": sort_by, "direction": sort_order}]

    response = await notion.databases.query(**params)

    rows = []
    for page in response.get("results", []):
        row = {
            "id": page["id"],
            "url": page["url"],
            "title": get_page_title(page),
            "created": page["created_time"],
            "last_edited": page["last_edited_time"],
            "properties": {},
        }
        for prop_name, prop_data in page.get("properties", {}).items():
            if prop_data.get("type") == "title":
                continue
            row["properties"][prop_name] = parse_property_value(prop_data)
        rows.append(row)

    return {
        "database_id": db_id,
        "total_returned": len(rows),
        "has_more": response.get("has_more", False),
        "rows": rows,
    }


async def add_database_row(
    database_id_or_url: str,
    properties: Dict[str, Any],
    content: str = "",
) -> dict:
    """Add a new row to a database."""
    notion = get_notion_client()
    db_id = extract_id(database_id_or_url)
    schema = await _get_schema(db_id)

    notion_properties = build_properties(schema, properties)

    children = []
    if content:
        from ..helpers.markdown_to_blocks import markdown_to_blocks
        children = markdown_to_blocks(content)[:100]

    new_page = await notion.pages.create(
        parent={"database_id": db_id},
        properties=notion_properties,
        children=children,
    )

    return {
        "success": True,
        "id": new_page["id"],
        "url": new_page["url"],
        "title": properties.get("Topic")
                  or properties.get("Title")
                  or properties.get("Name")
                  or "New Row",
        "message": "✅ Row added successfully",
    }


async def update_database_row(
    page_id_or_url: str,
    properties: Dict[str, Any],
) -> dict:
    """Update properties of an existing database row."""
    notion = get_notion_client()
    page_id = extract_id(page_id_or_url)

    page = await notion.pages.retrieve(page_id=page_id)
    parent = page.get("parent", {})

    if parent.get("type") != "database_id":
        raise ValueError("This page is not a database row")

    schema = await _get_schema(parent["database_id"])
    notion_properties = build_properties(schema, properties)

    await notion.pages.update(page_id=page_id, properties=notion_properties)

    return {
        "success": True,
        "id": page_id,
        "updated_fields": list(properties.keys()),
        "message": f"✅ Updated {len(properties)} field(s)",
    }


async def bulk_add_rows(
    database_id_or_url: str,
    rows: List[Dict[str, Any]],
) -> dict:
    """Add multiple rows to a database at once."""
    notion = get_notion_client()
    db_id = extract_id(database_id_or_url)
    schema = await _get_schema(db_id)

    created = []
    failed = []

    for i, row_props in enumerate(rows):
        try:
            notion_properties = build_properties(schema, row_props)
            new_page = await notion.pages.create(
                parent={"database_id": db_id},
                properties=notion_properties,
            )
            created.append({
                "id": new_page["id"],
                "title": row_props.get("Topic")
                          or row_props.get("Title")
                          or row_props.get("Name")
                          or f"Row {i+1}",
            })
        except Exception as e:
            failed.append({
                "index": i,
                "data": row_props,
                "error": str(e),
            })

    return {
        "success": len(failed) == 0,
        "total_added": len(created),
        "total_failed": len(failed),
        "created": created,
        "failed": failed,
        "message": f"✅ Added {len(created)}/{len(rows)} rows"
                   + (f" ({len(failed)} failed)" if failed else ""),
    }
