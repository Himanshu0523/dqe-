"""PS §2: Multi-table catalog, hydrated from disk. No single-table assumption."""
import sqlite3
from pathlib import Path
from dqe import config
from dqe.contracts import Column, Schema

_CATALOG: dict[str, Schema] = {}


def register(schema: Schema) -> None:
    _CATALOG[schema.table_name] = schema


def get(table: str) -> Schema | None:
    return _CATALOG.get(table)


def all_schemas() -> list[Schema]:
    return list(_CATALOG.values())


def has_any() -> bool:
    return bool(_CATALOG)


def _infer_from_sqlite(db_path: Path) -> list[Schema]:
    out: list[Schema] = []
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        try:
            tables = [
                r[0] for r in conn.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                ).fetchall()
            ]
            for table in tables:
                info = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
                row_count = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                cols: list[Column] = []
                for cid, name, ctype, notnull, dflt, pk in info:
                    t = (ctype or "").upper()
                    if "INT" in t:
                        dtype = "int64"
                    elif any(k in t for k in ("REAL", "FLOA", "DOUB")):
                        dtype = "float64"
                    elif any(k in t for k in ("DATE", "TIME")):
                        dtype = "datetime"
                    elif "BOOL" in t:
                        dtype = "bool"
                    else:
                        dtype = "string"
                    sample = [
                        r[0] for r in conn.execute(
                            f'SELECT "{name}" FROM "{table}" '
                            f'WHERE "{name}" IS NOT NULL LIMIT 3'
                        ).fetchall()
                    ]
                    cols.append(Column(name=name, dtype=dtype,
                                       nullable=not bool(notnull), sample=sample))
                pk_col = None
                for cid, name, ctype, notnull, dflt, pk in info:
                    if pk:
                        pk_col = name
                        break
                indexed = [r[1] for r in conn.execute(
                    f'PRAGMA index_list("{table}")').fetchall()]
                out.append(Schema(
                    table_name=table,
                    columns=cols,
                    primary_key=pk_col,
                    row_count=row_count,
                    indexed_columns=indexed,
                ))
        finally:
            conn.close()
    except Exception:
        pass
    return out


def hydrate() -> None:
    """Repopulate catalog from every .sqlite file in data/uploads/. Call at CLI start."""
    if _CATALOG:
        return
    for db in config.DATA_DIR.glob("*.sqlite"):
        for schema in _infer_from_sqlite(db):
            _CATALOG[schema.table_name] = schema