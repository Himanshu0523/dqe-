"""PS §3: Prompt-ready description of every loaded table (supports joins)."""
from dqe.contracts import Schema


def build_context(schemas: list[Schema]) -> str:
    if not schemas:
        return "No tables loaded."
    lines = [f"You have access to {len(schemas)} table(s). Use only these:\n"]
    for s in schemas:
        lines.append(f"TABLE {s.table_name}  (rows={s.row_count})")
        for c in s.columns:
            null = "NULL" if c.nullable else "NOT NULL"
            sample = ", ".join(repr(v) for v in c.sample[:3])
            lines.append(f"  {c.name}  {c.dtype}  {null}  e.g. {sample}")
        if s.primary_key:
            lines.append(f"  PRIMARY KEY: {s.primary_key}")
        if s.indexed_columns:
            lines.append(f"  INDEXED: {', '.join(s.indexed_columns)}")
        lines.append("")
    return "\n".join(lines)


def table_names(schemas: list[Schema]) -> list[str]:
    return [s.table_name for s in schemas]