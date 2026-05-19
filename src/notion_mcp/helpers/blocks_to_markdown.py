"""Convert Notion blocks to markdown text."""

from typing import List, Dict, Any


def rich_text_to_markdown(rich_text: List[Dict[str, Any]]) -> str:
    """Convert Notion rich_text array to markdown string."""
    if not rich_text:
        return ""

    result = []
    for rt in rich_text:
        text = rt.get("plain_text", "")
        ann = rt.get("annotations", {})
        href = rt.get("href")

        # Apply formatting in correct order
        if ann.get("code"):
            text = f"`{text}`"
        if ann.get("bold"):
            text = f"**{text}**"
        if ann.get("italic"):
            text = f"*{text}*"
        if ann.get("strikethrough"):
            text = f"~~{text}~~"
        if href:
            text = f"[{text}]({href})"

        result.append(text)

    return "".join(result)


def block_to_markdown(block: Dict[str, Any], indent: int = 0) -> str:
    """Convert a single Notion block to markdown."""
    block_type = block.get("type")
    indent_str = "  " * indent

    if block_type == "paragraph":
        text = rich_text_to_markdown(block["paragraph"]["rich_text"])
        return f"{indent_str}{text}" if text else ""

    elif block_type == "heading_1":
        text = rich_text_to_markdown(block["heading_1"]["rich_text"])
        return f"# {text}"

    elif block_type == "heading_2":
        text = rich_text_to_markdown(block["heading_2"]["rich_text"])
        return f"## {text}"

    elif block_type == "heading_3":
        text = rich_text_to_markdown(block["heading_3"]["rich_text"])
        return f"### {text}"

    elif block_type == "bulleted_list_item":
        text = rich_text_to_markdown(block["bulleted_list_item"]["rich_text"])
        return f"{indent_str}- {text}"

    elif block_type == "numbered_list_item":
        text = rich_text_to_markdown(block["numbered_list_item"]["rich_text"])
        return f"{indent_str}1. {text}"

    elif block_type == "to_do":
        text = rich_text_to_markdown(block["to_do"]["rich_text"])
        checked = "x" if block["to_do"].get("checked") else " "
        return f"{indent_str}- [{checked}] {text}"

    elif block_type == "quote":
        text = rich_text_to_markdown(block["quote"]["rich_text"])
        return f"> {text}"

    elif block_type == "code":
        text = rich_text_to_markdown(block["code"]["rich_text"])
        lang = block["code"].get("language", "")
        return f"```{lang}\n{text}\n```"

    elif block_type == "divider":
        return "---"

    elif block_type == "callout":
        text = rich_text_to_markdown(block["callout"]["rich_text"])
        icon = block["callout"].get("icon", {}).get("emoji", "💡")
        return f"> {icon} {text}"

    elif block_type == "toggle":
        text = rich_text_to_markdown(block["toggle"]["rich_text"])
        return f"{indent_str}▸ {text}"

    elif block_type == "image":
        url = block["image"].get("file", {}).get("url") or block["image"].get("external", {}).get("url", "")
        return f"![Image]({url})"

    elif block_type == "bookmark":
        url = block["bookmark"].get("url", "")
        return f"🔖 [{url}]({url})"

    elif block_type == "child_page":
        title = block["child_page"].get("title", "Untitled")
        return f"📄 **{title}** (sub-page)"

    elif block_type == "child_database":
        title = block["child_database"].get("title", "Untitled")
        return f"🗂 **{title}** (database)"

    else:
        return f"[Unsupported block: {block_type}]"


def blocks_to_markdown(blocks: List[Dict[str, Any]]) -> str:
    """Convert a list of Notion blocks to a markdown string."""
    lines = []
    for block in blocks:
        md = block_to_markdown(block)
        if md:
            lines.append(md)
    return "\n\n".join(lines)