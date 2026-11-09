"""PS §3(b): Rich table rendering."""
from rich.console import Console
from rich.table import Table
from dqe.contracts import ResultSet


def render(rs: ResultSet, title: str = "Results") -> None:
    console = Console()
    if rs.error:
        console.print(f"[red]Error:[/red] {rs.error}")
        return
    if not rs.columns:
        console.print("[yellow]Query returned no columns.[/yellow]")
        return
    table = Table(title=title, show_lines=False)
    for c in rs.columns:
        table.add_column(str(c))
    for row in rs.rows[:200]:  # visual cap; full data still in rs.rows
        table.add_row(*[str(v) if v is not None else "NULL" for v in row])
    console.print(table)
    note = f"  ({rs.row_count} rows"
    if rs.truncated:
        note += f", truncated at {rs.row_count}"
    if len(rs.rows) > 200:
        note += ", display capped at 200"
    note += ")"
    console.print(note)