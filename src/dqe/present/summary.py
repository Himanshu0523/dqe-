"""PS §3(b): One-line summary (deterministic, no LLM)."""
from dqe.contracts import ResultSet


def one_liner(rs: ResultSet) -> str:
    if rs.error:
        return f"Query failed: {rs.error}"
    return f"{rs.row_count} row(s) in {rs.elapsed_ms} ms" + (" (truncated)" if rs.truncated else "")