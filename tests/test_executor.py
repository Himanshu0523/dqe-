"""PS §5: row cap + read-only safety."""
from pathlib import Path
from dqe.ingest.registry import load_file
from dqe.store.sqlite_store import SQLiteStore
from dqe.store import indexer

FIX = Path(__file__).parent / "fixtures"


def test_row_cap(tmp_path):
    df, schema = load_file(FIX / "sample.csv")
    store = SQLiteStore(tmp_path / "t.sqlite")
    store.create_table(df, schema)
    indexer.auto_index(store, df, schema)
    # cross join → many rows
    rs = store.execute("SELECT a.id, b.id FROM sample a CROSS JOIN sample b")
    assert rs.error is None
    assert rs.row_count <= 10_000


def test_readonly_blocks_writes(tmp_path):
    df, schema = load_file(FIX / "sample.csv")
    store = SQLiteStore(tmp_path / "t.sqlite")
    store.create_table(df, schema)
    rs = store.execute("DELETE FROM sample")
    assert rs.error is not None  # read-only connection rejects