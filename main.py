"""
HR Leave Management MCP Server
--------------------------------
Exposes employee leave data (balances, applications, history) as MCP tools
so an LLM client (e.g. Claude Desktop) can answer HR queries in natural
language and take actions like applying for leave.

Run locally:
    uv run main.py

Install into Claude Desktop:
    uv run mcp install main.py
"""

import json
from datetime import datetime, date
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

mcp = FastMCP("HR Leave Management")

DATA_FILE = Path(__file__).parent / "employee_data.json"


def _load_data() -> dict:
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def _save_data(data: dict) -> None:
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def get_leave_balance(employee_id: str) -> str:
    """
    Get the remaining leave balance for an employee, broken down by leave type
    (casual, sick, earned).

    Args:
        employee_id: The employee's unique ID, e.g. "E001".
    """
    data = _load_data()
    employee = data.get(employee_id)
    if not employee:
        return f"No employee found with ID '{employee_id}'."

    balance = employee["leave_balance"]
    lines = [f"Leave balance for {employee['name']} ({employee_id}):"]
    for leave_type, days in balance.items():
        lines.append(f"  - {leave_type.capitalize()}: {days} day(s)")
    return "\n".join(lines)


@mcp.tool()
def apply_leave(
    employee_id: str,
    leave_type: str,
    start_date: str,
    end_date: str,
    reason: str,
) -> str:
    """
    Apply for leave on behalf of an employee. Deducts the requested number of
    days from that leave type's balance if enough days are available, and
    records the request in the employee's leave history with status
    'approved' (auto-approved for demo purposes).

    Args:
        employee_id: The employee's unique ID, e.g. "E001".
        leave_type: One of "casual", "sick", or "earned".
        start_date: Leave start date in YYYY-MM-DD format.
        end_date: Leave end date in YYYY-MM-DD format (inclusive).
        reason: Short reason for the leave request.
    """
    data = _load_data()
    employee = data.get(employee_id)
    if not employee:
        return f"No employee found with ID '{employee_id}'."

    leave_type = leave_type.lower()
    if leave_type not in employee["leave_balance"]:
        valid = ", ".join(employee["leave_balance"].keys())
        return f"Invalid leave type '{leave_type}'. Valid types: {valid}."

    try:
        start = _parse_date(start_date)
        end = _parse_date(end_date)
    except ValueError:
        return "Dates must be in YYYY-MM-DD format."

    if end < start:
        return "end_date cannot be before start_date."

    requested_days = (end - start).days + 1
    available = employee["leave_balance"][leave_type]

    if requested_days > available:
        return (
            f"Cannot apply: requested {requested_days} day(s) of {leave_type} "
            f"leave but only {available} day(s) available."
        )

    # Deduct balance and record history
    employee["leave_balance"][leave_type] -= requested_days
    employee["leave_history"].append({
        "leave_type": leave_type,
        "start_date": start_date,
        "end_date": end_date,
        "days": requested_days,
        "reason": reason,
        "status": "approved",
        "applied_on": date.today().isoformat(),
    })

    _save_data(data)

    return (
        f"Leave applied for {employee['name']} ({employee_id}): "
        f"{requested_days} day(s) of {leave_type} leave from {start_date} "
        f"to {end_date}. Remaining {leave_type} balance: "
        f"{employee['leave_balance'][leave_type]} day(s)."
    )


@mcp.tool()
def get_leave_history(employee_id: str) -> str:
    """
    Retrieve the full leave application history for an employee, most recent
    first.

    Args:
        employee_id: The employee's unique ID, e.g. "E001".
    """
    data = _load_data()
    employee = data.get(employee_id)
    if not employee:
        return f"No employee found with ID '{employee_id}'."

    history = employee["leave_history"]
    if not history:
        return f"{employee['name']} ({employee_id}) has no leave history yet."

    lines = [f"Leave history for {employee['name']} ({employee_id}):"]
    for entry in reversed(history):
        lines.append(
            f"  - {entry['leave_type'].capitalize()} leave: "
            f"{entry['start_date']} to {entry['end_date']} "
            f"({entry['days']} day(s)) — {entry['status']} — {entry['reason']}"
        )
    return "\n".join(lines)


@mcp.tool()
def list_employees() -> str:
    """
    List all employees in the system with their ID, name, and department.
    Useful for the LLM to look up an employee's ID when the user only gives
    a name.
    """
    data = _load_data()
    lines = ["Employees on record:"]
    for emp_id, emp in data.items():
        lines.append(f"  - {emp_id}: {emp['name']} ({emp['department']})")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
