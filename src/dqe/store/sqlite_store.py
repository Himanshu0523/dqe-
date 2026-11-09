from __future__ import annotations
import sqlite3
import time
from pathlib import Path
import pandas as pd

from dqe import config
from dqe.contracts import Schema, ResultSet


class SQLiteStore:
    dialect = config.DIALECT

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    # ---- ingest (write) ----
    def create_table(self, df: pd.DataFrame, schema: Schema) -> None:
        conn = sqlite3.connect(str(self.db_path))
        try:
            df.to_sql(schema.table_name, conn, if_exists="replace", index=False)
        finally:
            conn.close()

    def create_index(self, table: str, column: str) -> None:
        conn = sqlite3.connect(str(self.db_path))
        try:
            idx = f"idx_{table}_{column}"
            conn.execute(f'CREATE INDEX IF NOT EXISTS "{idx}" ON "{table}" ("{column}")')
            conn.commit()
        finally:
            conn.close()

    #  query (read-only) 
    def _connect_ro(self) -> sqlite3.Connection:
        # PS §5: read-only enforced at connection level
        return sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)

    def execute(self, sql: str, timeout_s: float = config.QUERY_TIMEOUT_S) -> ResultSet:
        start = time.perf_counter()
        conn = self._connect_ro()
        deadline = time.time() + timeout_s

        def _progress() -> int:
            return 1 if time.time() > deadline else 0

        conn.set_progress_handler(_progress, 1000)
        try:
            cur = conn.execute(sql)
            cols = [d[0] for d in cur.description] if cur.description else []
            rows = cur.fetchmany(config.MAX_ROWS_RETURNED + 1)
            truncated = len(rows) > config.MAX_ROWS_RETURNED
            rows = rows[: config.MAX_ROWS_RETURNED]
            elapsed = (time.perf_counter() - start) * 1000
            return ResultSet(
                columns=cols, rows=list(rows), row_count=len(rows),
                elapsed_ms=round(elapsed, 2), sql_executed=sql,
                truncated=truncated,
            )
        except sqlite3.OperationalError as e:
            msg = str(e)
            if "interrupted" in msg.lower() or "timeout" in msg.lower():
                msg = f"Query timeout after {timeout_s}s"
            return ResultSet(columns=[], rows=[], row_count=0,
                             elapsed_ms=round((time.perf_counter()-start)*1000, 2),
                             sql_executed=sql, error=msg)
        except sqlite3.Error as e:
            return ResultSet(columns=[], rows=[], row_count=0,
                             elapsed_ms=round((time.perf_counter()-start)*1000, 2),
                             sql_executed=sql, error=str(e))
        finally:
            conn.close()

    def explain(self, sql: str) -> str:
        conn = self._connect_ro()
        try:
            cur = conn.execute(f"EXPLAIN QUERY PLAN {sql}")
            return "\n".join("  " + " | ".join(str(c) for c in row) for row in cur.fetchall())
        except sqlite3.Error as e:
            return f"(explain failed: {e})"
        finally:
            conn.close()