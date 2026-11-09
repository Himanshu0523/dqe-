"""PS §3: Domain examples for LLM prompting and template fallback tests."""

EXAMPLES = [
    {"q": "show all rows", "sql": "SELECT * FROM {table} LIMIT 100"},
    {"q": "how many rows are there", "sql": "SELECT COUNT(*) AS n FROM {table}"},
    {"q": "top 5 rows by {col}", "sql": "SELECT * FROM {table} ORDER BY {col} DESC LIMIT 5"},
    {"q": "average {col}", "sql": "SELECT AVG({col}) AS avg_{col} FROM {table}"},
    {"q": "count by {col}", "sql": "SELECT {col}, COUNT(*) AS n FROM {table} GROUP BY {col} ORDER BY n DESC"},
]