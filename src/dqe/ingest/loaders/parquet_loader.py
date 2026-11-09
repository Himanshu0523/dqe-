"""PS §1: Parquet loader."""
import pandas as pd
from pathlib import Path


def load(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path)