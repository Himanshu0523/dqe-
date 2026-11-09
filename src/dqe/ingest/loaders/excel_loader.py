"""PS §1: Excel loader (first sheet)."""
import pandas as pd
from pathlib import Path


def load(path: Path) -> pd.DataFrame:
    return pd.read_excel(path, sheet_name=0)