from __future__ import annotations
import pandas as pd
from dqe.contracts import Schema
from dqe.store.sqlite_store import SQLiteStore


def auto_index(store: SQLiteStore, df: pd.DataFrame, schema: Schema) -> list[str]:
    candidates: set[str] = set()
    if schema.primary_key:
        candidates.add(schema.primary_key)
    for col in schema.columns:
        if col.dtype in ("datetime", "int64"):
            candidates.add(col.name)
        # cardinality heuristic: 2 ≤ unique ≤ 10k → good filter candidate
        s = df[col.name]
        nun = s.nunique(dropna=True)
        if 2 <= nun <= 10_000:
            candidates.add(col.name)
    for col in candidates:
        store.create_index(schema.table_name, col)
    schema.indexed_columns = sorted(candidates)
    return schema.indexed_columns