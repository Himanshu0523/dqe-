from __future__ import annotations
import pandas as pd
from dqe.contracts import Column , Schema


DTYPE_MAP = {
    "int64": "int64", "Int64": "int64",
    "float64": "float64", "Float64": "float64",
    "bool": "bool", "boolean": "bool",
    "object": "string", "string": "string",
    "datetime64[ns]": "datetime",
}


def _infer_dtype(series: pd.Series) -> str:
    return DTYPE_MAP.get(str(series.dtype), "string")


def _candidate_pk(df: pd.DataFrame) -> str | None:
    for col in df.columns:
        s = df[col]
        if s.isna().any():
            continue
        if s.nunique() == len(df) and len(df) > 0:
            return col
    return None

def infer_schema(df: pd.DataFrame, table_name: str) -> Schema:
    columns = []
    for col in df.columns:
        s = df[col]
        sample = [v for v in s.dropna().head(3).tolist()]
        columns.append(Column(
            name=str(col),
            dtype=_infer_dtype(s),
            nullable=bool(s.isna().any()),
            sample=sample,
        ))
    return Schema(
        table_name=table_name,
        columns=columns,
        primary_key=_candidate_pk(df),
        row_count=len(df),
    )