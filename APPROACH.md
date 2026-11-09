# Approach and System Architecture

## DQE — Universal Dataset Query Engine

## 1. Overview

The Universal Dataset Query Engine (DQE) follows a modular architecture that converts natural-language questions into validated SQL queries and executes them against structured datasets.

The architecture separates the system into independent components:

- Dataset ingestion
- Data storage
- Schema inference
- Natural-language processing
- SQL generation
- SQL validation
- Query optimization
- Query execution
- Result presentation

This separation improves maintainability, testability, and the ability to replace individual components without redesigning the entire application.

## 2. High-Level Architecture

```text
                 USER
                  |
                  v
       +----------------------+
       | CLI / Streamlit UI   |
       +----------------------+
                  |
                  v
       +----------------------+
       | Dataset Ingestion    |
       | CSV / JSON / Excel   |
       | Parquet / SQLite     |
       +----------------------+
                  |
                  v
       +----------------------+
       | Schema Inference     |
       | Tables / Columns     |
       | Data Types / Metadata|
       +----------------------+
                  |
                  v
       +----------------------+
       | Data Storage         |
       | SQLite               |
       +----------------------+
                  |
                  v
       +----------------------+
       | Natural Language     |
       | Query Processing     |
       +----------------------+
                  |
                  v
       +----------------------+
       | SQL Generation       |
       | LLM / Template       |
       +----------------------+
                  |
                  v
       +----------------------+
       | SQL Parsing &        |
       | Validation           |
       +----------------------+
                  |
                  v
       +----------------------+
       | Query Optimization   |
       | Rule-Based           |
       +----------------------+
                  |
                  v
       +----------------------+
       | Safe Query Execution |
       | Read-Only SQLite     |
       +----------------------+
                  |
                  v
       +----------------------+
       | Result Presentation  |
       | Table / Chart / SQL  |
       | Optimization Details |
       +----------------------+
                  |
                  v
                 USER
```

## 3. Core Processing Pipeline

### Step 1: Dataset Ingestion

**Purpose:** Accept datasets in different structured formats.

Supported input formats:

- CSV
- JSON
- Excel
- Parquet
- SQLite

Responsibilities:

1. Identify the input format.
2. Validate the uploaded file.
3. Read the dataset.
4. Normalize data into an internal representation.
5. Handle missing or inconsistent values where supported.
6. Pass the processed data to the storage layer.

Expected module:

```text
src/dqe/ingest/
```

### Step 2: Schema Inference

**Purpose:** Understand the structure of the dataset before generating queries.

The schema inference component identifies:

- Table names
- Column names
- Data types
- Available fields
- Relevant metadata

Example schema:

```text
Table: sales

Columns:
- order_id: INTEGER
- product_name: TEXT
- category: TEXT
- quantity: INTEGER
- revenue: REAL
- order_date: DATE
```

Schema information is provided to the natural-language-to-SQL component so that generated queries can reference available database objects.

### Step 3: Data Storage

**Purpose:** Store normalized datasets in a queryable database.

DQE uses SQLite as its execution database.

Responsibilities:

- Create the required tables.
- Store normalized dataset records.
- Maintain schema information.
- Provide a controlled database connection.
- Support read-only query execution.

Expected module:

```text
src/dqe/store/
```

### Step 4: Natural-Language Processing

**Purpose:** Convert a user's question into a structured query-generation request.

Example:

```text
User:
Show the top 5 products by revenue.
```

The system uses the question and available schema information to determine the required operation.

The query-generation stage must consider:

- Relevant table
- Relevant columns
- Filtering conditions
- Aggregation requirements
- Sorting requirements
- Result limit

### Step 5: SQL Generation

DQE supports two SQL-generation approaches.

#### A. LLM-Based Generation

An LLM can interpret natural-language questions and generate SQL using the supplied schema context.

Configured provider options include:

- Gemini
- OpenAI
- xAI

The provider and model configuration should be controlled through environment variables.

#### B. Template-Based Fallback

A template-based fallback provides a non-LLM generation path for supported query patterns.

Examples of supported patterns may include:

- Show all rows.
- Return the first N rows.
- Filter records by a condition.
- Sort records by a column.
- Calculate aggregates.
- Group records by a column.

The fallback must reject unsupported or ambiguous requests rather than generate arbitrary SQL.

Expected module:

```text
src/dqe/nl2query/
```

### Step 6: SQL Parsing and Validation

**Purpose:** Ensure that generated SQL is syntactically valid and permitted before execution.

Validation should include:

1. Parse the generated SQL.
2. Confirm that the query belongs to the permitted statement class.
3. Reject non-SELECT statements.
4. Reject multiple statements.
5. Validate referenced tables and columns where supported.
6. Reject unsupported SQL constructs.
7. Apply configured query restrictions.

The execution policy is SELECT-only.

Examples of statements that must be rejected:

```sql
DROP TABLE sales;
```

```sql
DELETE FROM sales;
```

```sql
UPDATE sales
SET revenue = 0;
```

A query must not reach the execution layer unless it passes validation.

Expected module:

```text
src/dqe/query/
```

### Step 7: Query Optimization

**Purpose:** Improve query execution through supported rule-based transformations.

The optimization component analyzes the validated SQL and applies eligible rules.

Potential optimization areas include:

- Removing unnecessary operations.
- Simplifying supported expressions.
- Reducing unnecessary selected columns.
- Applying filters earlier where semantics are preserved.
- Avoiding unnecessary sorting.
- Applying result limits where appropriate.

Each transformation must preserve query semantics.

The system should retain information about:

- Original SQL
- Optimized SQL
- Applied optimization rules
- Optimization decisions
- Relevant execution-plan differences

Optimization must not be assumed to improve every query. Performance improvements should be measured.

Expected module:

```text
src/dqe/query/
```

### Step 8: Safe Query Execution

**Purpose:** Execute validated and optimized SQL under controlled conditions.

Execution requirements:

- Use read-only database access.
- Apply a 5-second execution timeout.
- Enforce a maximum result limit of 10,000 rows.
- Handle execution errors.
- Prevent unsupported operations from reaching the database.

The execution component returns query results and relevant execution information to the presentation layer.

Expected module:

```text
src/dqe/execute/
```

### Step 9: Result Presentation

**Purpose:** Present query results in an understandable format.

The presentation layer can provide:

- Tabular results
- Generated SQL
- Optimized SQL
- Charts where suitable
- Optimization logs
- Query execution information
- Plan differences where available

Example:

```text
Question:
Show the top 3 products by revenue.

Generated SQL:
SELECT product_name, SUM(revenue) AS total_revenue
FROM sales
GROUP BY product_name
ORDER BY total_revenue DESC
LIMIT 3;

Result:
+--------------+---------------+
| product_name | total_revenue |
+--------------+---------------+
| Product A    | 95000         |
| Product B    | 78000         |
| Product C    | 64000         |
+--------------+---------------+
```

The values above are illustrative and are not benchmark results.

Expected module:

```text
src/dqe/present/
```

## 4. Module Structure

```text
src/
└── dqe/
    ├── ingest/
    │   └── Dataset ingestion
    │
    ├── store/
    │   └── Database storage
    │
    ├── nl2query/
    │   └── Natural language to SQL
    │
    ├── query/
    │   └── Parsing, validation,
    │       and optimization
    │
    ├── execute/
    │   └── Safe query execution
    │
    ├── present/
    │   └── Result presentation
    │
    └── cli.py
        └── Command-line interface

web/
├── app.py
├── voice.py
└── state.py

tests/
├── fixtures/
└── Test modules

bench/
└── latency.py
```

## 5. Query Processing Contract

The processing pipeline should follow this order:

```text
Input Dataset
     |
     v
Ingestion
     |
     v
Schema Inference
     |
     v
Storage
     |
     v
Natural Language Question
     |
     v
SQL Generation
     |
     v
SQL Parsing
     |
     v
SQL Validation
     |
     v
Optimization
     |
     v
Execution
     |
     v
Result Presentation
```

Important rules:

- Invalid SQL must not be executed.
- Non-SELECT statements must be rejected.
- Query limits must be enforced.
- Optimization must preserve query semantics.
- Execution errors must be handled without exposing sensitive internal details.
- The system must not treat LLM-generated SQL as trusted input.

## 6. Error Handling Strategy

The system should handle failures at each processing stage.

| Component        | Possible Failure           | Expected Handling                        |
| ---------------- | -------------------------- | ---------------------------------------- |
| Ingestion        | Invalid file               | Return validation error                  |
| Schema inference | Unsupported structure      | Report schema error                      |
| Storage          | Database failure           | Return storage error                     |
| SQL generation   | Provider unavailable       | Use supported fallback or report failure |
| SQL parsing      | Invalid SQL                | Reject query                             |
| SQL validation   | Unsafe operation           | Block execution                          |
| Optimization     | Unsupported transformation | Keep validated original query            |
| Execution        | Timeout                    | Stop execution and report timeout        |
| Presentation     | Unsupported chart          | Display tabular results                  |

Fallback behavior should be implemented and tested explicitly.

## 7. Configuration

The application uses environment variables for provider configuration.

Example:

```env
DQE_LLM_PROVIDER=gemini

GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=your_configured_model

OPENAI_API_KEY=your_openai_api_key
XAI_API_KEY=your_xai_api_key
```

Keep actual credentials in a local environment file.

Do not commit API keys or secrets to GitHub.

## 8. Testing Strategy

Testing should cover each major component independently.

### Unit Testing

- Dataset ingestion
- Schema inference
- SQL generation
- SQL parsing
- SQL validation
- Query optimization
- Query execution

### Integration Testing

- Dataset upload to storage.
- Natural-language question to SQL.
- SQL validation to execution.
- Query execution to result presentation.

### Security Testing

- Reject non-SELECT statements.
- Reject multiple SQL statements.
- Test malformed SQL.
- Test excessive result requests.
- Test execution timeouts.
- Test unsupported query constructs.

### Performance Testing

Measure:

- Dataset ingestion time.
- SQL generation latency.
- Query execution latency.
- Optimization overhead.
- Total request latency.

## 9. Design Principles

DQE follows these architectural principles:

1. **Modularity:** Each component has a defined responsibility.
2. **Separation of Concerns:** Query generation and execution remain independent.
3. **Security by Design:** Generated SQL is treated as untrusted input.
4. **Fallback Support:** Supported fallback behavior reduces dependence on external LLM providers.
5. **Transparency:** SQL and optimization decisions are inspectable.
6. **Testability:** Components can be tested independently.
7. **Extensibility:** New input formats and query-generation providers can be added through defined interfaces.

## 10. Conclusion

DQE uses a modular query-processing architecture to bridge natural-language interaction and structured-data querying.

The architecture combines multiple ingestion formats, schema inference, LLM-based or template-based SQL generation, validation, rule-based optimization, controlled SQLite execution, and result presentation.

Its primary design objective is to make data querying accessible without compromising execution safety or transparency.
