"""Productivity shortcuts - smart workflows combining multiple operations."""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from ..client import get_notion_client
from ..helpers.url_parser import extract_id, get_page_title
from ..helpers.markdown_to_blocks import markdown_to_blocks
from ..helpers.property_builder import build_properties, parse_property_value
from ..config import DEFAULT_PARENT_PAGE_ID


async def _find_database_by_name(name_keywords: List[str]) -> Optional[dict]:
    """Find a database whose title contains any keyword (case-insensitive)."""
    notion = get_notion_client()
    response = await notion.search(
        filter={"property": "object", "value": "database"},
        page_size=100,
    )

    for db in response.get("results", []):
        title_arr = db.get("title", [])
        title = "".join(t.get("plain_text", "") for t in title_arr).lower()
        for keyword in name_keywords:
            if keyword.lower() in title:
                return db
    return None


async def quick_note(content: str, title: Optional[str] = None) -> dict:
    """Create a quick note under DEFAULT_PARENT_PAGE_ID with timestamp."""
    notion = get_notion_client()
    if not DEFAULT_PARENT_PAGE_ID:
        raise ValueError(
            "DEFAULT_PARENT_PAGE_ID not set in .env. "
            "Set it to your preferred 'inbox' page ID."
        )

    parent_id = extract_id(DEFAULT_PARENT_PAGE_ID)
    now = datetime.now()

    if not title:
        title = f"📝 Note - {now.strftime('%b %d, %Y %H:%M')}"

    children = markdown_to_blocks(content) if content else []

    new_page = await notion.pages.create(
        parent={"page_id": parent_id},
        properties={
            "title": [{"type": "text", "text": {"content": title}}]
        },
        children=children[:100],
    )

    return {
        "success": True,
        "id": new_page["id"],
        "url": new_page["url"],
        "title": title,
        "message": "✅ Quick note saved",
    }


async def daily_journal(entry: str, journal_keyword: str = "journal") -> dict:
    """Append a timestamped entry to today's journal page."""
    notion = get_notion_client()
    response = await notion.search(
        query=journal_keyword,
        filter={"property": "object", "value": "page"},
        page_size=10,
    )

    journal_page = None
    for page in response.get("results", []):
        title = get_page_title(page).lower()
        if journal_keyword.lower() in title:
            journal_page = page
            break

    if not journal_page:
        raise ValueError(
            f"No page found with '{journal_keyword}' in title. "
            "Create a 'Daily Journal' page and share with integration."
        )

    now = datetime.now()
    timestamped = f"### {now.strftime('%A, %B %d, %Y - %H:%M')}\n\n{entry}\n\n---"

    blocks = markdown_to_blocks(timestamped)

    await notion.blocks.children.append(
        block_id=journal_page["id"],
        children=blocks,
    )

    return {
        "success": True,
        "journal_page": get_page_title(journal_page),
        "timestamp": now.isoformat(),
        "blocks_added": len(blocks),
        "message": f"📔 Entry added to {get_page_title(journal_page)}",
    }


async def add_task(
    title: str,
    due_date: Optional[str] = None,
    priority: Optional[str] = None,
    status: str = "Not Started",
    tags: Optional[List[str]] = None,
) -> dict:
    """Quick-add a task to your Tasks database (auto-detected)."""
    notion = get_notion_client()
    db = await _find_database_by_name(["task", "todo", "to-do"])
    if not db:
        raise ValueError("No tasks database found. Create one with 'Task' in name.")

    schema = {
        name: {"type": data.get("type")}
        for name, data in db.get("properties", {}).items()
    }

    title_prop = next(
        (k for k, v in schema.items() if v["type"] == "title"),
        "Name"
    )

    properties = {title_prop: title}

    for prop_name, prop_info in schema.items():
        prop_lower = prop_name.lower()
        ptype = prop_info["type"]

        if "status" in prop_lower and ptype in ("status", "select") and status:
            properties[prop_name] = status
        elif "priority" in prop_lower and ptype in ("select", "status") and priority:
            properties[prop_name] = priority
        elif ("due" in prop_lower or "date" in prop_lower) and ptype == "date" and due_date:
            properties[prop_name] = due_date
        elif "tag" in prop_lower and ptype == "multi_select" and tags:
            properties[prop_name] = tags

    notion_properties = build_properties(schema, properties)

    new_page = await notion.pages.create(
        parent={"database_id": db["id"]},
        properties=notion_properties,
    )

    db_title = "".join(t.get("plain_text", "") for t in db.get("title", []))

    return {
        "success": True,
        "id": new_page["id"],
        "url": new_page["url"],
        "task": title,
        "database": db_title,
        "properties_set": list(properties.keys()),
        "message": f"✅ Task '{title}' added to {db_title}",
    }


async def get_today_tasks() -> dict:
    """Get all tasks due today or earlier (overdue)."""
    notion = get_notion_client()
    db = await _find_database_by_name(["task", "todo", "to-do"])
    if not db:
        raise ValueError("No tasks database found.")

    schema = {
        name: {"type": data.get("type")}
        for name, data in db.get("properties", {}).items()
    }

    today = date.today().isoformat()

    date_prop = next(
        (name for name, info in schema.items()
         if info["type"] == "date" and ("due" in name.lower() or "date" in name.lower())),
        None
    )

    query_params = {"database_id": db["id"], "page_size": 100}

    if date_prop:
        query_params["filter"] = {
            "property": date_prop,
            "date": {"on_or_before": today},
        }

    response = await notion.databases.query(**query_params)

    tasks = []
    for page in response.get("results", []):
        task_data = {
            "id": page["id"],
            "title": get_page_title(page),
            "url": page["url"],
        }
        for prop_name, prop_data in page.get("properties", {}).items():
            if prop_data.get("type") == "title":
                continue
            task_data[prop_name] = parse_property_value(prop_data)
        tasks.append(task_data)

    return {
        "date": today,
        "total_tasks": len(tasks),
        "tasks": tasks,
        "message": f"📋 {len(tasks)} task(s) for today or overdue",
    }


async def complete_task(task_name_or_id: str) -> dict:
    """Mark a task as complete by name or ID."""
    notion = get_notion_client()
    page = None

    try:
        page_id = extract_id(task_name_or_id)
        page = await notion.pages.retrieve(page_id=page_id)
    except Exception:
        db = await _find_database_by_name(["task", "todo"])
        if not db:
            raise ValueError("No tasks database found.")

        response = await notion.databases.query(
            database_id=db["id"],
            page_size=100,
        )

        for p in response.get("results", []):
            if task_name_or_id.lower() in get_page_title(p).lower():
                page = p
                break

        if not page:
            raise ValueError(f"Task '{task_name_or_id}' not found")

    status_prop_name = None
    status_type = None
    for prop_name, prop_data in page.get("properties", {}).items():
        if prop_data.get("type") in ("status", "select") and "status" in prop_name.lower():
            status_prop_name = prop_name
            status_type = prop_data.get("type")
            break

    if not status_prop_name:
        raise ValueError("No status property found on task")

    done_value = "Done"
    parent = page.get("parent", {})
    if parent.get("type") == "database_id":
        db = await notion.databases.retrieve(database_id=parent["database_id"])
        options = db["properties"][status_prop_name].get(status_type, {}).get("options", [])
        for opt in options:
            if opt["name"].lower() in ("done", "complete", "completed", "finished"):
                done_value = opt["name"]
                break

    await notion.pages.update(
        page_id=page["id"],
        properties={
            status_prop_name: {status_type: {"name": done_value}}
        },
    )

    return {
        "success": True,
        "task": get_page_title(page),
        "status": done_value,
        "message": f"✅ Task '{get_page_title(page)}' marked as {done_value}",
    }


async def get_recent_pages(limit: int = 10) -> dict:
    """Get recently edited pages."""
    notion = get_notion_client()
    response = await notion.search(
        filter={"property": "object", "value": "page"},
        sort={"direction": "descending", "timestamp": "last_edited_time"},
        page_size=min(limit, 100),
    )

    pages = []
    for page in response.get("results", []):
        pages.append({
            "id": page["id"],
            "title": get_page_title(page),
            "url": page["url"],
            "last_edited": page.get("last_edited_time"),
        })

    return {
        "total": len(pages),
        "pages": pages,
        "message": f"📚 {len(pages)} recently edited pages",
    }


async def learning_dashboard() -> dict:
    """Get a dashboard view of your AI/ML learning progress."""
    notion = get_notion_client()
    db = await _find_database_by_name(["topic", "learning", "ai/ml", "ai", "ml"])
    if not db:
        raise ValueError(
            "No learning database found. Create one with 'Topics' or 'Learning' in the name."
        )

    response = await notion.databases.query(
        database_id=db["id"],
        page_size=100,
    )

    rows = response.get("results", [])
    total = len(rows)

    # Group by status
    status_counts: Dict[str, int] = {}
    category_counts: Dict[str, int] = {}
    priority_counts: Dict[str, int] = {}
    progress_total = 0
    progress_count = 0

    by_status: Dict[str, list] = {}

    for page in rows:
        title = get_page_title(page)
        props = page.get("properties", {})

        for prop_name, prop_data in props.items():
            ptype = prop_data.get("type")
            value = parse_property_value(prop_data)

            if ptype == "status" and "status" in prop_name.lower() and value:
                status_counts[value] = status_counts.get(value, 0) + 1
                by_status.setdefault(value, []).append(title)
            elif ptype == "select" and "category" in prop_name.lower() and value:
                category_counts[value] = category_counts.get(value, 0) + 1
            elif ptype == "select" and "priority" in prop_name.lower() and value:
                priority_counts[value] = priority_counts.get(value, 0) + 1
            elif ptype == "number" and "progress" in prop_name.lower() and value is not None:
                progress_total += value
                progress_count += 1

    avg_progress = (progress_total / progress_count) if progress_count else 0

    return {
        "database": "".join(t.get("plain_text", "") for t in db.get("title", [])),
        "total_topics": total,
        "by_status": status_counts,
        "by_category": category_counts,
        "by_priority": priority_counts,
        "average_progress": round(avg_progress, 1),
        "topics_by_status": by_status,
        "message": f"🎓 {total} topics tracked, {avg_progress:.0f}% avg progress",
    }
