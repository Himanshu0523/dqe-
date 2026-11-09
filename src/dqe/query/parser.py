"""PS §3(a): Wrap sqlglot parsing."""
from __future__ import annotations
import sqlglot
from sqlglot import exp
from dqe import config


def parse(sql: str, dialect: str = config.DIALECT) -> exp.Expression:
    return sqlglot.parse_one(sql, dialect=dialect)


def parse_many(sql: str, dialect: str = config.DIALECT) -> list[exp.Expression]:
    return sqlglot.parse(sql, dialect=dialect)