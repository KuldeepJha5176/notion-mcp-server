"""Comments operations for Notion pages."""

from ..client import notion
from ..helpers.url_parser import extract_id


async def add_comment(page_id_or_url: str, comment_text: str) -> dict:
    """Add a comment to a Notion page."""
    page_id = extract_id(page_id_or_url)

    response = await notion.comments.create(
        parent={"page_id": page_id},
        rich_text=[{"type": "text", "text": {"content": comment_text}}],
    )

    return {
        "success": True,
        "comment_id": response["id"],
        "page_id": page_id,
        "message": "💬 Comment added",
    }


async def get_comments(page_id_or_url: str) -> dict:
    """Get all comments on a page."""
    page_id = extract_id(page_id_or_url)

    response = await notion.comments.list(block_id=page_id)

    comments = []
    for comment in response.get("results", []):
        rich_text = comment.get("rich_text", [])
        text = "".join(t.get("plain_text", "") for t in rich_text)
        comments.append({
            "id": comment["id"],
            "text": text,
            "created": comment.get("created_time"),
            "created_by": comment.get("created_by", {}).get("id"),
        })

    return {
        "page_id": page_id,
        "total_comments": len(comments),
        "comments": comments,
    }