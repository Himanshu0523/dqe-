"""PS §3(a): Rule-based optimizer with human-readable change log."""
from __future__ import annotations
from sqlglot import exp
from dqe import config
from dqe.contracts import Schema, OptimizedQuery
from dqe.query import parser


def _has_limit(node: exp.Expression) -> bool:
    return node.find(exp.Limit) is not None


def _add_limit(node: exp.Expression, n: int) -> exp.Expression:
    return node.limit(n)


def _prune_star(node: exp.Expression, schema: Schema) -> exp.Expression:
    """Replace top-level SELECT * with explicit columns only when a WHERE exists."""
    if not isinstance(node, exp.Select):
        return node
    stars = list(node.find_all(exp.Star))
    if not stars:
        return node
    if node.find(exp.Where) is None:
        return node  # keep * if no filter; user wants to see the data
    cols = ", ".join(f'"{c}"' for c in schema.column_names())
    new_sql = node.sql(dialect=config.DIALECT)
    new_sql = new_sql.replace("*", cols, 1)
    return parser.parse(new_sql)


def _constant_fold(node: exp.Expression) -> exp.Expression:
    try:
        return node.transform(
            lambda n: n.eval() if isinstance(n, exp.Binary) and not n.find(exp.Column) else n
        ) or node
    except Exception:
        return node


def optimize(sql: str, schemas: list[Schema], dialect: str = config.DIALECT) -> OptimizedQuery:
    changes: list[str] = []
    node = parser.parse(sql, dialect)
    folded = _constant_fold(node)
    if folded.sql(dialect=dialect) != node.sql(dialect=dialect):
        changes.append("constant-folded expressions")
        node = folded
    pruned = _prune_star(node, schemas)
    if pruned.sql(dialect=dialect) != node.sql(dialect=dialect):
        changes.append("pruned SELECT * to explicit columns")
        node = pruned
    if not _has_limit(node):
        node = _add_limit(node, config.DEFAULT_LIMIT)
        changes.append(f"added LIMIT {config.DEFAULT_LIMIT}")
    return OptimizedQuery(sql=node.sql(dialect=dialect), changes=changes)



def _prune_star(node: exp.Expression, schemas: list[Schema]) -> exp.Expression:
    if not isinstance(node, exp.Select):
        return node
    if not list(node.find_all(exp.Star)):
        return node
    if node.find(exp.Where) is None:
        return node
    tables = [t.name for t in node.find_all(exp.Table) if t.name]
    if len(tables) != 1:
        return node
    schema = next((s for s in schemas if s.table_name == tables[0]), None)
    if not schema:
        return node
    cols = ", ".join(f'"{c}"' for c in schema.column_names())
    new_sql = node.sql(dialect=config.DIALECT).replace("*", cols, 1)
    return parser.parse(new_sql)