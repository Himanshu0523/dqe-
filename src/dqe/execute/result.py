"""PS §3(b): Result formatting helpers used by the CLI."""
from dqe.contracts import ResultSet


def is_error(rs: ResultSet) -> bool:
    return rs.error is not None


def has_numeric_column(rs: ResultSet) -> bool:
    for row in rs.rows[:1]:
        for v in row:
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                return True
    return False