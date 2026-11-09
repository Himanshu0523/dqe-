import json
import pandas as pd
from pathlib import Path


def load(path: Path) -> pd.DataFrame:
    if path.suffix == ".jsonl":
        return pd.read_json(path, lines=True)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        # If dict of lists, treat as columns; else wrap
        try:
            return pd.json_normalize(data)
        except Exception:
            return pd.DataFrame([data])
    return pd.json_normalize(data)