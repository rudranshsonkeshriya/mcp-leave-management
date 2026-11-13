# HR Leave Management MCP Server

A Model Context Protocol (MCP) server that lets an LLM (via Claude Desktop)
act as an HR assistant — checking leave balances, applying for leave, and
pulling leave history for employees, backed by a simple JSON "database".

## Project structure

```
mcp_leave_management/
├── main.py              # MCP server: defines the tools
├── employee_data.json   # Mock employee database
├── pyproject.toml       # Project dependencies
└── README.md
```

## 1. Environment setup

Install [uv](https://docs.astral.sh/uv/) if you don't have it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh      # macOS/Linux
# or: pip install uv
```

From inside the project folder, sync dependencies:

```bash
cd mcp_leave_management
uv sync
```

This reads `pyproject.toml` and installs the `mcp` SDK into a local
virtual environment.

## 2. Run the server directly (optional sanity check)

```bash
uv run main.py
```

This starts the server over stdio. It won't print much — that's normal,
it's waiting for a client (like Claude Desktop) to connect.

## 3. Install into Claude Desktop

```bash
uv run mcp install main.py
```

This registers the server in Claude Desktop's config file
(`claude_desktop_config.json`) automatically. Then:

1. Open Claude Desktop.
2. Go to **Settings → Developer** and make sure Developer Mode is enabled,
   so you can see and manage installed MCP servers.
3. Restart Claude Desktop.
4. You should see "HR Leave Management" listed as a connected MCP server
   (look for the hammer/tools icon in a new chat).

## 4. Try it out

Ask Claude things like:

- "How many leave days does E001 have left?"
- "Apply 2 days of casual leave for E002 from 2026-10-05 to 2026-10-06 for a family event."
- "Show me E003's leave history."
- "List all employees."

Claude will match your request to the right tool (`get_leave_balance`,
`apply_leave`, `get_leave_history`, `list_employees`), extract the right
arguments from your sentence, and call it — you can watch it ask for
confirmation before running each tool.

## Available tools

| Tool | Purpose |
|---|---|
| `get_leave_balance(employee_id)` | Returns remaining casual/sick/earned leave |
| `apply_leave(employee_id, leave_type, start_date, end_date, reason)` | Applies for leave, deducts balance, logs to history |
| `get_leave_history(employee_id)` | Returns all past leave applications |
| `list_employees()` | Lists all employee IDs, names, departments |

## Why the docstrings matter

Each tool's docstring is what the LLM reads to decide *which* tool to call
and *how* to fill in its arguments from a natural-language request. Keep
them precise — describe each argument's format explicitly (e.g. "YYYY-MM-DD")
since that's exactly what the model uses to parse dates out of your sentence.

## Ideas to extend for your final-year submission

These are good "extra depth" additions once the base server works, each a
natural talking point in your report/demo:

- **Role-based access**: add a `manager_id` check so only a manager can
  approve/reject a *pending* leave (currently auto-approved for simplicity).
- **`get_team_calendar(manager_id, start_date, end_date)`**: show who on a
  manager's team is on leave in a date range — demos nicely as a "team view".
- **Swap JSON for SQLite**: same tool logic, but backed by a real database —
  a good point to discuss persistence and concurrency in your report.
- **Email notification (mocked)**: print/log a "notification sent" message
  when leave is applied or approved, to simulate a production system.
- **Input validation edge cases**: overlapping leave dates, leave in the past,
  more than N days in a single request — good for a "robustness" demo slide.

## Demo script for presentation day

1. `list_employees()` → show the data model.
2. `get_leave_balance("E001")` → show current state.
3. `apply_leave("E001", "casual", "2026-10-05", "2026-10-06", "Personal work")`
   → show balance decreasing.
4. `get_leave_history("E001")` → show the new entry logged.
5. Try an invalid case (e.g. more days than available) → show graceful error
   handling — this is often what gets extra credit.
