"""PS §1, §2: ingestion + schema inference."""
from pathlib import Path
from dqe.ingest.registry import load_file

FIX = Path(__file__).parent / "fixtures"


def test_csv_ingest():
    df, schema = load_file(FIX / "sample.csv")
    assert schema.row_count == 10
    assert "revenue" in schema.column_names()
    assert schema.primary_key == "id"
    assert any(c.name == "date" for c in schema.columns)