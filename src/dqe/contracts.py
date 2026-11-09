from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Column:
    name: str
    dtype: str                
    nullable: bool
    sample: list[Any] = field(default_factory=list)


@dataclass
class Schema:
    table_name: str
    columns: list[Column]
    primary_key: str | None
    row_count: int
    indexed_columns: list[str] = field(default_factory=list)

    def column_names(self) -> list[str]:
        return [c.name for c in self.columns]

    def has_column(self, name: str) -> bool:
        return name in self.column_names()


@dataclass
class ValidationResult:
    ok: bool
    reason: str | None
    sql: str


@dataclass
class OptimizedQuery:
    sql: str
    changes: list[str] = field(default_factory=list)


@dataclass
class ResultSet:
    columns: list[str]
    rows: list[tuple]
    row_count: int
    elapsed_ms: float
    sql_executed: str
    plan: str | None = None
    truncated: bool = False
    error: str | None = None