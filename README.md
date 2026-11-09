
# dqe — Universal Dataset Query Engine

Upload any tabular file, ask questions in natural language (typed or spoken), and receive validated, optimized SQL queries with results — using a read-only execution path.

## Quickstart

### 1. Install dependencies

```bash
pip install -e ".[dev,llm]"
```

### 2. Run tests

```bash
pytest -q
```

### 3. Upload a dataset

```bash
dqe upload tests/fixtures/sample.csv
```

### 4. Ask a question

```bash
dqe ask "top 3 rows by revenue"
```

### Configure an LLM provider

For free-form natural-language questions, configure an API key in your `.env` file:

```env
GEMINI_API_KEY=your-key
DQE_LLM_PROVIDER=gemini
```

Then run:

```bash
dqe ask "which categories earned the most?"
```

## What It Does

| Stage    | What happens                                                                                         |
| -------- | ---------------------------------------------------------------------------------------------------- |
| Upload   | CSV, JSON, Excel, Parquet, and SQLite files are loaded with inferred schemas and indexes.            |
| Ask      | Natural language is translated into SQL using Gemini, Grok, OpenAI, or an offline template provider. |
| Validate | AST-based validation checks that queries are read-only and reference known tables and columns.       |
| Optimize | Applies query optimization rules such as LIMIT injection, projection pruning, and constant folding.  |
| Execute  | Executes queries using a read-only connection, a 5-second timeout, and a 10,000-row result limit.    |
| Present  | Displays results, SQL, optimization logs, charts, and query plan comparisons.                        |

## Why It's Different

Existing tools generally solve individual parts of the dataset-querying workflow. DQE combines them into one pipeline:

- **Automatic schema inference:** No manual table definition is required.
- **Natural Language to SQL:** Convert user questions into SQL queries.
- **Pre-execution validation:** Validate SQL before execution to prevent unsafe operations.
- **Rule-based optimization:** Apply optimization rules and explain the changes.
- **Query plan comparison:** Display `EXPLAIN QUERY PLAN` results before and after optimization.
- **Offline fallback:** Run supported queries without an external API using the template provider.
- **Read-only execution:** Protect the underlying SQLite database against write operations.

See [PROBLEM_STATEMENT.md](PROBLEM_STATEMENT.md) for the formal problem definition and gap analysis.

## Architecture

```text
User Input (Natural Language / SQL)
              |
              v
          Ingestion
              |
              v
            Store
              |
              v
          NL to SQL
              |
              v
        Query Validation
              |
              v
        Query Optimization
              |
              v
           Execution
              |
              v
           Presentation
              |
              v
        Results and Explanation
```

The core processing pipeline is:

```text
ingest → store → nl2query → query → execute → present
```

Each module has a defined responsibility and interface.

See:

- [APPROACH.md](APPROACH.md) — Architecture and design decisions.
- [EVALUATION.md](EVALUATION.md) — Testing and performance evaluation.

## Usage

### CLI

#### Upload a dataset

```bash
dqe upload data.csv
```

#### Ask questions in natural language

```bash
dqe ask "which categories earned the most?"
```

#### Execute raw SQL

Raw SQL queries also pass through validation and optimization.

```bash
dqe query "SELECT category, SUM(revenue) FROM data GROUP BY category"
```

#### Select an LLM provider

```bash
dqe ask "top 5 by revenue" --provider gemini
dqe ask "top 5 by revenue" --provider grok
dqe ask "top 5 by revenue" --provider template
```

### Web UI

Start the Streamlit application:

```bash
streamlit run web/app.py
```

Open the application:

[http://localhost:8501](http://localhost:8501)

The interface provides a four-panel workflow:

1. **Input:** Upload a dataset.
2. **Preview:** Inspect the dataset and inferred schema.
3. **Ask:** Enter a natural-language question or use speech input.
4. **Results:** View generated SQL, results, optimization details, and query plans.

## Supported Formats

| Format       | Extensions            | Description                                    |
| ------------ | --------------------- | ---------------------------------------------- |
| CSV          | `.csv`              | Comma-separated tabular data.                  |
| JSON / JSONL | `.json`, `.jsonl` | JSON records with one-level nested flattening. |
| Excel        | `.xlsx`, `.xls`   | Reads the first worksheet.                     |
| Parquet      | `.parquet`          | Columnar data format.                          |
| SQLite       | `.db`, `.sqlite`  | Reads the first user table.                    |

## Configuration

Create a `.env` file in the project root.

```env
DQE_LLM_PROVIDER=gemini

GEMINI_API_KEY=your-gemini-api-key
XAI_API_KEY=your-xai-api-key
OPENAI_API_KEY=your-openai-api-key

GEMINI_MODEL=gemini-2.5-flash
```

### Environment Variables

| Variable             | Purpose                           |
| -------------------- | --------------------------------- |
| `DQE_LLM_PROVIDER` | Selects the default LLM provider. |
| `GEMINI_API_KEY`   | Gemini API authentication.        |
| `XAI_API_KEY`      | Grok API authentication.          |
| `OPENAI_API_KEY`   | OpenAI API authentication.        |
| `GEMINI_MODEL`     | Specifies the Gemini model.       |

**Security:** API keys must be loaded from environment variables. Never hardcode credentials in source code or commit your `.env` file to GitHub.

Use `.env.example` to document the required environment variables without exposing actual credentials.

## Testing

Run all tests:

```bash
pytest -q
```

Run individual test suites:

```bash
# Validator tests
pytest tests/test_validator.py -v

# End-to-end tests
pytest tests/test_e2e.py -v

# Ingestion tests
pytest tests/test_ingest.py -v

# Optimizer tests
pytest tests/test_optimizer.py -v

# Executor tests
pytest tests/test_executor.py -v
```

Run the latency benchmark:

```bash
python bench/latency.py
```

## Project Structure

```text
dataset_query_engine/
│
├── PROBLEM_STATEMENT.md
├── APPROACH.md
├── EVALUATION.md
├── README.md
│
├── pyproject.toml
├── .env.example
│
├── src/
│   └── dqe/
│       ├── ingest/
│       ├── store/
│       ├── nl2query/
│       ├── query/
│       ├── execute/
│       ├── present/
│       └── cli.py
│
├── web/
│   ├── app.py
│   ├── voice.py
│   └── state.py
│
├── tests/
│   ├── test_ingest.py
│   ├── test_validator.py
│   ├── test_optimizer.py
│   ├── test_executor.py
│   └── test_e2e.py
│
└── bench/
    └── latency.py
```

## Constraints and Security

The project is designed around the following constraints:

- **Read-only execution:** SQLite read-only mode prevents database write operations.
- **Query timeout:** A 5-second execution limit enforced using SQLite's `set_progress_handler`.
- **Result limit:** Maximum of 10,000 returned rows, with truncation information.
- **Offline support:** The template provider works without external API calls.
- **SQL validation:** AST-based validation restricts queries to supported read-only operations.
- **Credential security:** API keys are managed through environment variables.
- **Input limits:** Maximum input size of 1 GB and 20 columns.

See [EVALUATION.md](EVALUATION.md) for the test strategy and validation measurements.

## Documentation

| Document                                    | Description                                                           |
| ------------------------------------------- | --------------------------------------------------------------------- |
| [PROBLEM_STATEMENT.md](PROBLEM_STATEMENT.md) | Problem definition, existing gaps, constraints, and success criteria. |
| [APPROACH.md](APPROACH.md)                   | Architecture, module responsibilities, and design decisions.          |
| [EVALUATION.md](EVALUATION.md)               | Evaluation methodology, benchmarks, and known limitations.            |
| [README.md](README.md)                       | Installation, configuration, usage, and project overview.             |

## License

This project is licensed under the MIT License.
