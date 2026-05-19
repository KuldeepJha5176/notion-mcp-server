"""Convert markdown text to Notion blocks."""

import re
from typing import List, Dict, Any


def parse_inline_formatting(text: str) -> List[Dict[str, Any]]:
    """
    Parse inline markdown formatting (bold, italic, code, links).
    Returns Notion rich_text array.
    """
    if not text:
        return []

    rich_text = []
    # Pattern matches: **bold**, *italic*, `code`, [link](url)
    pattern = r'(\*\*[^\*]+\*\*|\*[^\*]+\*|`[^`]+`|\[[^\]]+\]\([^\)]+\))'
    parts = re.split(pattern, text)

    for part in parts:
        if not part:
            continue

        annotations = {
            "bold": False,
            "italic": False,
            "code": False,
            "strikethrough": False,
            "underline": False,
            "color": "default",
        }
        link = None
        content = part

        # Bold: **text**
        if part.startswith("**") and part.endswith("**"):
            content = part[2:-2]
            annotations["bold"] = True
        # Italic: *text*
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            content = part[1:-1]
            annotations["italic"] = True
        # Code: `text`
        elif part.startswith("`") and part.endswith("`"):
            content = part[1:-1]
            annotations["code"] = True
        # Link: [text](url)
        elif part.startswith("[") and "](" in part:
            match = re.match(r'\[([^\]]+)\]\(([^\)]+)\)', part)
            if match:
                content = match.group(1)
                link = {"url": match.group(2)}

        rich_text.append({
            "type": "text",
            "text": {"content": content, "link": link},
            "annotations": annotations,
            "plain_text": content,
        })

    return rich_text


def markdown_to_blocks(markdown: str) -> List[Dict[str, Any]]:
    """
    Convert markdown string to a list of Notion block objects.

    Supports:
        # H1, ## H2, ### H3
        - bullet list
        1. numbered list
        - [ ] / - [x] todos
        > blockquote
        ```code blocks```
        ---  divider
        Plain paragraphs
        Inline: **bold**, *italic*, `code`, [link](url)
    """
    if not markdown or not markdown.strip():
        return []

    blocks = []
    lines = markdown.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            i += 1
            continue

        # Code block ```lang ... ```
        if stripped.startswith("```"):
            lang = stripped[3:].strip() or "plain text"
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            blocks.append({
                "object": "block",
                "type": "code",
                "code": {
                    "rich_text": [{"type": "text", "text": {"content": "\n".join(code_lines)}}],
                    "language": lang.lower() if lang.lower() in VALID_LANGUAGES else "plain text",
                },
            })
            i += 1
            continue

        # Divider: ---
        if stripped == "---" or stripped == "***":
            blocks.append({"object": "block", "type": "divider", "divider": {}})
            i += 1
            continue

        # Heading 3: ###
        if stripped.startswith("### "):
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": parse_inline_formatting(stripped[4:])},
            })
            i += 1
            continue

        # Heading 2: ##
        if stripped.startswith("## "):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": parse_inline_formatting(stripped[3:])},
            })
            i += 1
            continue

        # Heading 1: #
        if stripped.startswith("# "):
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": parse_inline_formatting(stripped[2:])},
            })
            i += 1
            continue

        # To-do unchecked: - [ ]
        if re.match(r"^[-*]\s+\[\s\]\s+", stripped):
            text = re.sub(r"^[-*]\s+\[\s\]\s+", "", stripped)
            blocks.append({
                "object": "block",
                "type": "to_do",
                "to_do": {
                    "rich_text": parse_inline_formatting(text),
                    "checked": False,
                },
            })
            i += 1
            continue

        # To-do checked: - [x]
        if re.match(r"^[-*]\s+\[x\]\s+", stripped, re.IGNORECASE):
            text = re.sub(r"^[-*]\s+\[x\]\s+", "", stripped, flags=re.IGNORECASE)
            blocks.append({
                "object": "block",
                "type": "to_do",
                "to_do": {
                    "rich_text": parse_inline_formatting(text),
                    "checked": True,
                },
            })
            i += 1
            continue

        # Bullet list: - or *
        if re.match(r"^[-*]\s+", stripped):
            text = re.sub(r"^[-*]\s+", "", stripped)
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": parse_inline_formatting(text)},
            })
            i += 1
            continue

        # Numbered list: 1. 2. etc.
        if re.match(r"^\d+\.\s+", stripped):
            text = re.sub(r"^\d+\.\s+", "", stripped)
            blocks.append({
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {"rich_text": parse_inline_formatting(text)},
            })
            i += 1
            continue

        # Blockquote: >
        if stripped.startswith("> "):
            blocks.append({
                "object": "block",
                "type": "quote",
                "quote": {"rich_text": parse_inline_formatting(stripped[2:])},
            })
            i += 1
            continue

        # Default: paragraph
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": parse_inline_formatting(stripped)},
        })
        i += 1

    return blocks


# Notion supported code languages (subset of common ones)
VALID_LANGUAGES = {
    "abap", "arduino", "bash", "basic", "c", "clojure", "coffeescript",
    "c++", "c#", "css", "dart", "diff", "docker", "elixir", "elm", "erlang",
    "flow", "fortran", "f#", "gherkin", "glsl", "go", "graphql", "groovy",
    "haskell", "html", "java", "javascript", "json", "julia", "kotlin",
    "latex", "less", "lisp", "livescript", "lua", "makefile", "markdown",
    "markup", "matlab", "mermaid", "nix", "objective-c", "ocaml", "pascal",
    "perl", "php", "plain text", "powershell", "prolog", "protobuf", "python",
    "r", "reason", "ruby", "rust", "sass", "scala", "scheme", "scss", "shell",
    "sql", "swift", "typescript", "vb.net", "verilog", "vhdl", "visual basic",
    "webassembly", "xml", "yaml",
}