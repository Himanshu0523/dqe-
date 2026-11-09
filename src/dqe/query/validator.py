"""PS §6: whitelist SELECT, single statement, every table and column must exist."""
from __future__ import annotations
from sqlglot import exp

from dqe import config
from dqe.contracts import Schema, ValidationResult
from dqe.query import parser

FORBIDDEN = (
    exp.Drop, exp.Create, exp.Alter, exp.Insert, exp.Update, exp.Delete,
    exp.Command, exp.Attach, exp.Detach,
)


def validate(sql: str, schemas: list[Schema], dialect: str = config.DIALECT) -> ValidationResult:
    sql = sql.strip()
    if not sql:
        return ValidationResult(False, "empty SQL", sql)
    if ";" in sql.rstrip(";"):
        return ValidationResult(False, "multiple statements not allowed", sql)
    try:
        statements = parser.parse_many(sql, dialect)
    except Exception as e:
        return ValidationResult(False, f"parse error: {e}", sql)
    if len(statements) != 1:
        return ValidationResult(False, "multiple statements not allowed", sql)
    stmt = statements[0]
    if not isinstance(stmt, (exp.Select, exp.Union)):
        return ValidationResult(False, f"only SELECT allowed, got {type(stmt).__name__}", sql)

    for node in stmt.walk():
        if isinstance(node, FORBIDDEN):
            return ValidationResult(False, f"forbidden node: {type(node).__name__}", sql)

    known_tables = {s.table_name for s in schemas}
    table_aliases: set[str] = set()
    for tbl in stmt.find_all(exp.Table):
        name = tbl.name
        if not name:
            continue
        if name not in known_tables:
            return ValidationResult(False, f"unknown table: {name}", sql)
        if tbl.alias:
            table_aliases.add(tbl.alias)

    known_cols: set[str] = set()
    for s in schemas:
        known_cols.update(s.column_names())
    aliases = {a.alias_or_name for a in stmt.find_all(exp.Alias) if a.alias}
    aliases |= {a.alias_or_name for a in stmt.find_all(exp.Star)}

    for col in stmt.find_all(exp.Column):
        name = col.name
        if not name:
            continue
        if name in known_cols or name in aliases or name in table_aliases:
            continue
        if name.isdigit():
            continue
        return ValidationResult(False, f"unknown column: {name}", sql)

    return ValidationResult(True, None, sql)