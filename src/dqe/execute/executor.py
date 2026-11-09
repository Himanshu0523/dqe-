"""PS §5: Thin dispatch over SQLiteStore; timeout and row cap live in the store."""
from __future__ import annotations
from dqe.contracts import ResultSet
from dqe.store.sqlite_store import SQLiteStore


def execute(store: SQLiteStore, sql: str) -> ResultSet:
    return store.execute(sql)