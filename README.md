# Notion MCP Server

> 🚀 Powerful Notion integration for Claude — read, create, search, and manage your entire Notion workspace through natural language.

[![PyPI version](https://img.shields.io/pypi/v/notion-mcp-server.svg)](https://pypi.org/project/notion-mcp-server/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)

## ✨ Features

- 🔍 **Smart Search** — Find pages and databases instantly
- 📄 **Page Management** — Create, read, update, archive, duplicate pages
- 🎨 **Full Markdown Support** — Seamless markdown ↔ Notion blocks conversion
- 🗂 **Database Operations** — Query with filters, sort, bulk add rows
- ⚡ **Productivity Shortcuts** — Quick notes, daily journal, task management
- 🧱 **Block-Level Control** — Read, update, delete individual blocks
- 💬 **Comments Support** — Add and read page comments
- 🎓 **Learning Dashboard** — Track AI/ML or any learning database progress
- 🔒 **Privacy First** — All pages private by default
- ⚡ **Fast & Async** — Built with FastMCP, schema caching, auto-retry

## 🎬 What You Can Do

Ask Claude things like:

- *"Search my Notion for 'machine learning'"*
- *"Create a page called 'Project Plan' with a roadmap"*
- *"Add 20 AI/ML topics to my Topics database"*
- *"Show me all tasks marked Critical priority"*
- *"What's on my schedule today?"*
- *"Add a quick note: meeting was great"*
- *"Show my learning dashboard"*

## 📦 Installation

### Prerequisites

- Python 3.10 or higher
- A Notion account
- Claude Desktop, Claude Code, or any MCP-compatible client

### Install with uv (recommended)

\`\`\`bash
uv tool install notion-mcp-server
\`\`\`

### Install with pip

\`\`\`bash
pip install notion-mcp-server
\`\`\`

## 🔧 Setup (5 minutes)

### Step 1: Create a Notion Integration

1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click **"+ New integration"**
3. Name it (e.g., "Claude MCP")
4. Select your workspace
5. Click **Submit**
6. Copy the **Internal Integration Secret** (starts with `secret_` or `ntn_`)

### Step 2: Share Pages with Integration

For each page or database you want Claude to access:

1. Open the page in Notion
2. Click **"..."** menu (top right)
3. Click **"Connections"** → **"Connect to"**
4. Select your integration

> 💡 **Pro tip:** Sharing a parent page automatically gives access to all sub-pages. Create one "Workspace Hub" page and share that.

### Step 3: Configure Claude Desktop

**Mac/Linux:**
\`\`\`bash
~/Library/Application\ Support/Claude/claude_desktop_config.json
\`\`\`

**Windows:**
\`\`\`
%APPDATA%\\Claude\\claude_desktop_config.json
\`\`\`

Add this configuration:

\`\`\`json
{
  "mcpServers": {
    "notion": {
      "command": "uvx",
      "args": ["notion-mcp-server"],
      "env": {
        "NOTION_TOKEN": "secret_your_token_here",
        "DEFAULT_PRIVACY": "private",
        "DEFAULT_PARENT_PAGE_ID": "optional_parent_page_id"
      }
    }
  }
}
\`\`\`

### Step 4: Restart Claude Desktop

**Fully quit** (including system tray) and reopen.

### Step 5: Test It!

Ask Claude:
> *"Check my Notion connection"*

If you see ✅ Connected — you're all set!

## 🛠 Available Tools (22 Total)

### 🔍 Search & Connection
- `search_notion(query, filter_type, limit)` — Search pages/databases
- `check_connection()` — Verify integration works

### 📄 Page Operations
- `get_page(page_id_or_url)` — Read page as markdown
- `create_page(title, parent_id, content, privacy)` — Create new page
- `append_to_page(page_id_or_url, content)` — Append content
- `update_page_title(page_id_or_url, new_title)` — Rename page
- `archive_page(page_id_or_url)` — Soft-delete page
- `restore_page(page_id_or_url)` — Restore archived page
- `duplicate_page(page_id_or_url, new_title)` — Clone page

### 🗂 Database Operations
- `list_databases()` — List all databases
- `get_database_schema(database_id_or_url)` — See columns and types
- `query_database(database_id_or_url, filters, sort_by, ...)` — Query rows
- `add_database_row(database_id_or_url, properties, content)` — Add row
- `update_database_row(page_id_or_url, properties)` — Update row
- `bulk_add_rows(database_id_or_url, rows)` — Add many rows at once

### 🧱 Block Operations
- `get_block_children(block_id_or_url)` — Read all blocks
- `update_block(block_id_or_url, new_content)` — Edit a block
- `delete_block(block_id_or_url)` — Delete a block

### 💬 Comments
- `add_comment(page_id_or_url, comment_text)` — Add a comment
- `get_comments(page_id_or_url)` — Read comments

### ⚡ Productivity Shortcuts
- `quick_note(content, title)` — Quick note to default parent
- `daily_journal(entry)` — Append timestamped entry to journal
- `add_task(title, due_date, priority, status, tags)` — Smart-add task
- `get_today_tasks()` — Tasks due today or overdue
- `complete_task(task_name_or_id)` — Mark task done
- `get_recent_pages(limit)` — Recently edited pages
- `learning_dashboard()` — Learning progress overview

## 🎨 Markdown Support

Full bidirectional conversion:

| Markdown | Notion Block |
|----------|--------------|
| `# Heading 1` | Heading 1 |
| `## Heading 2` | Heading 2 |
| `### Heading 3` | Heading 3 |
| `- bullet` | Bulleted list |
| `1. numbered` | Numbered list |
| `- [ ] todo` | To-do (unchecked) |
| `- [x] done` | To-do (checked) |
| `> quote` | Quote block |
| ` ```code``` ` | Code block |
| `---` | Divider |
| `**bold**` | Bold text |
| `*italic*` | Italic text |
| `` `inline code` `` | Inline code |
| `[link](url)` | Link |

## ⚙️ Configuration

| Environment Variable | Required | Description |
|---------------------|----------|-------------|
| \`NOTION_TOKEN\` | ✅ Yes | Your integration secret |
| \`DEFAULT_PRIVACY\` | ❌ No | \`private\` (default) or \`public\` |
| \`DEFAULT_PARENT_PAGE_ID\` | ❌ No | Default parent for new pages |

## 💡 Examples

### Example 1: Bulk Create Database Entries

> *"Add 20 AI/ML topics to my Topics database with appropriate categories and priorities"*

Claude uses \`bulk_add_rows\` to create all 20 entries with one command.

### Example 2: Daily Workflow

\`\`\`
You: "What tasks do I have today?"
Claude: [shows your today_tasks]

You: "Mark 'Review PR #123' as done"
Claude: [calls complete_task]

You: "Add a journal entry: Productive day, finished 5 tasks"
Claude: [appends to journal page]
\`\`\`

### Example 3: Smart Querying

> *"Show me high-priority topics that aren't started yet, sorted by category"*

Claude builds a complex filter and returns organized results.

## 🐛 Troubleshooting

### "Object not found" errors
The page/database isn't shared with your integration.
**Fix:** Open page → ... → Connections → Connect to your integration.

### Empty search results
You haven't shared any pages with the integration yet.
**Fix:** Share at least one page (and its sub-pages will inherit access).

### "Cannot create workspace-level page"
Internal integrations can't create pages at workspace root.
**Fix:** Set \`DEFAULT_PARENT_PAGE_ID\` in your config to a parent page.

### Rate limit errors
Notion API allows ~3 requests/second.
**Fix:** Server has built-in auto-retry with exponential backoff.

## 🤝 Contributing

Pull requests welcome! For major changes, please open an issue first.

\`\`\`bash
git clone https://github.com/KuldeepJha5176/notion-mcp-server
cd notion-mcp-server
uv sync
uv run pytest
\`\`\`

## 🔒 Security

- Each user provides their own Notion token
- Tokens stored locally in user's environment
- Server never collects, stores, or transmits user data
- All communication is direct: User → Notion API
- See [SECURITY.md](SECURITY.md) for vulnerability reporting

## 📄 License

MIT — see [LICENSE](LICENSE) file.

## 🙏 Acknowledgments

Built with:
- [FastMCP](https://github.com/jlowin/fastmcp) — Excellent MCP framework
- [notion-client](https://github.com/ramnes/notion-sdk-py) — Notion Python SDK
- [Anthropic MCP](https://modelcontextprotocol.io) — The protocol that makes it possible

## ⭐ Show Your Support

If this server helps you, please:
- ⭐ **Star** this repo
- 🐦 **Tweet** about it
- 📝 **Blog** about how you use it
- 🐛 **Report bugs** to make it better

---

**Made with ❤️ for the Claude community by [Kuldeep Jha](https://github.com/KuldeepJha5176)**