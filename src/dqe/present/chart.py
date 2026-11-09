"""PS §3(b): Auto chart — bar for categorical×numeric, line for date×numeric."""
from __future__ import annotations
from pathlib import Path
import pandas as pd
from dqe.contracts import ResultSet
from dqe import config


def maybe_chart(rs: ResultSet, name: str = "chart") -> Path | None:
    try:
        if rs.error or len(rs.rows) < 2 or len(rs.columns) < 2:
            return None
        df = pd.DataFrame(rs.rows, columns=rs.columns)
        num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        if not num_cols:
            return None
        num = num_cols[0]
        other = [c for c in df.columns if c != num][0]
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(7, 3.5))
        is_date = pd.api.types.is_datetime64_any_dtype(df[other])
        if is_date:
            ax.plot(df[other], df[num], marker="o")
        else:
            ax.bar(df[other].astype(str), df[num])
            ax.tick_params(axis="x", rotation=45)
        ax.set_ylabel(num)
        ax.set_title(f"{num} by {other}")
        fig.tight_layout()
        out = config.OUT_DIR / f"{name}.png"
        fig.savefig(out, dpi=120)
        plt.close(fig)
        return out
    except Exception:
        return None