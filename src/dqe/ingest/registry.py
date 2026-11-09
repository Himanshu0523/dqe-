from __future__ import annotations
from pathlib import Path
import pandas as pd

from dqe import config
from dqe.contracts import Schema
from dqe.ingest.normalize import normalize
from dqe.ingest.schema import infer_schema
from dqe.ingest.loaders import (
    csv_loader, json_loader, excel_loader, parquet_loader, sqlite_loader,
)

LOADERS = {
    ".csv": csv_loader.load,
    ".json": json_loader.load,
    ".jsonl": json_loader.load,
    ".xlsx": excel_loader.load,
    ".xls": excel_loader.load,
    ".parquet": parquet_loader.load,
    ".db": sqlite_loader.load,
    ".sqlite": sqlite_loader.load,
    ".sqlite3": sqlite_loader.load,
}


def load_file(path: Path, table_name: str | None = None) -> tuple[pd.DataFrame, Schema]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    if path.stat().st_size > config.MAX_FILE_BYTES:
        raise ValueError(f"File exceeds {config.MAX_FILE_BYTES} bytes")
    suffix = path.suffix.lower()
    if suffix not in LOADERS:
        raise ValueError(f"Unsupported extension: {suffix}. Supported: {list(LOADERS)}")
    df = LOADERS[suffix](path)
    df = normalize(df)
    name = table_name or path.stem.lower().replace(" ", "_").replace("-", "_")
    schema = infer_schema(df, name)
    return df, schema