from __future__ import annotations
import pandas as pd
from dqe import config


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Flatten any dict/list columns one level
    for col in list(df.columns):
        if df[col].apply(lambda x: isinstance(x, (dict, list))).any():
            df[col] = df[col].apply(lambda x: str(x) if isinstance(x, (dict, list)) else x)
    # Strip string whitespace
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
    # Try datetime coercion on object columns that look like dates
    for col in df.columns:
        if df[col].dtype == object:
            sample = df[col].dropna().head(20).tolist()
            if sample and all(isinstance(x, str) and len(x) >= 10 and x[4] == "-" for x in sample):
                try:
                    df[col] = pd.to_datetime(df[col], errors="ignore")
                except Exception:
                    pass
    # Column cap (PS §5)
    if len(df.columns) > config.MAX_COLUMNS:
        df = df.iloc[:, : config.MAX_COLUMNS]
    # Normalize column names
    df.columns = [str(c).strip().replace(" ", "_").lower() for c in df.columns]
    return df