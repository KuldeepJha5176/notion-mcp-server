"""Search tools for Notion."""

from ..client import get_notion_client
from ..helpers.url_parser import get_page_title


async def search_notion(
    query: str = "",
    filter_type: str = "all",
    limit: int = 20,
) -> dict:
    """
    Search across all Notion pages and databases shared with the integration.
    """
    notion = get_notion_client()
    search_params = {
        "query": query,
        "page_size": min(limit, 100),
    }

    if filter_type in ("page", "database"):
        search_params["filter"] = {
            "property": "object",
            "value": filter_type,
        }

    response = await notion.search(**search_params)

    results = []
    for item in response.get("results", []):
        obj_type = item.get("object")
        item_id = item.get("id")
        url = item.get("url", "")
        title = get_page_title(item)

        parent = item.get("parent", {})
        parent_type = parent.get("type", "workspace")

        results.append({
            "id": item_id,
            "type": obj_type,
            "title": title,
            "url": url,
            "parent_type": parent_type,
            "last_edited": item.get("last_edited_time"),
            "created": item.get("created_time"),
        })

    return {
        "query": query,
        "filter": filter_type,
        "total_results": len(results),
        "results": results,
    }
