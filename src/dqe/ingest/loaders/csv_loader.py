"""PS §1: CSV loader."""
import pandas as pd
from pathlib import Path


def load(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, low_memory=False)