"""PS §3(a): LIMIT injection, projection pruning, change log."""
from pathlib import Path
from dqe.ingest.registry import load_file
from dqe.query.optimizer import optimize

FIX = Path(__file__).parent / "fixtures"
_, SCHEMA = load_file(FIX / "sample.csv")


def test_limit_added():
    opt = optimize("SELECT * FROM sample", SCHEMA)
    assert "LIMIT" in opt.sql.upper()
    assert any("LIMIT" in c for c in opt.changes)


def test_projection_pruned_under_filter():
    opt = optimize("SELECT * FROM sample WHERE revenue > 100", SCHEMA)
    assert "*" not in opt.sql
    assert any("pruned" in c for c in opt.changes)