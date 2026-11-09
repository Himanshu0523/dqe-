"""PS §6: 0 unsafe statements pass validation."""
import pytest
from pathlib import Path
from dqe.ingest.registry import load_file
from dqe.query.validator import validate

FIX = Path(__file__).parent / "fixtures"
_, SCHEMA = load_file(FIX / "sample.csv")

UNSAFE = [
    "DROP TABLE sample",
    "DELETE FROM sample",
    "UPDATE sample SET revenue=0",
    "INSERT INTO sample VALUES (1,'x','y',1,'2024-01-01')",
    "CREATE TABLE evil (x int)",
    "ALTER TABLE sample ADD COLUMN x int",
    "ATTACH DATABASE 'x' AS y",
    "PRAGMA table_info(sample)",
    "SELECT 1; DROP TABLE sample",
    "SELECT * FROM sample; SELECT * FROM sample",
    "SELECT * FROM other_table",
    "SELECT nonexistent_col FROM sample",
]

@pytest.mark.parametrize("sql", UNSAFE)
def test_unsafe_rejected(sql):
    result = validate(sql, SCHEMA)
    assert not result.ok, f"should reject: {sql}"


SAFE = [
    "SELECT * FROM sample",
    "SELECT id, name FROM sample WHERE revenue > 100",
    "SELECT category, COUNT(*) AS n FROM sample GROUP BY category",
    "SELECT AVG(revenue) AS avg_revenue FROM sample",
    "SELECT * FROM sample ORDER BY revenue DESC LIMIT 5",
]

@pytest.mark.parametrize("sql", SAFE)
def test_safe_accepted(sql):
    result = validate(sql, SCHEMA)
    assert result.ok, f"should accept: {sql} -> {result.reason}"