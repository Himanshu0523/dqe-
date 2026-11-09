import sqlite3
import pandas as pd
from pathlib import Path


def load(path: Path) -> pd.DataFrame:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        tables = pd.read_sql_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'",
            conn,
        )["name"].tolist()
        if not tables:
            raise ValueError("No user tables found in SQLite file")
        return pd.read_sql_query(f'SELECT * FROM "{tables[0]}"', conn)
    finally:
        conn.close()