
# Evaluation and Testing

## DQE — Universal Dataset Query Engine

## 1. Introduction

This document describes the evaluation strategy for the Universal Dataset Query Engine (DQE).

The evaluation focuses on five important areas:

1. Query correctness
2. SQL execution safety
3. Query performance
4. User onboarding and usability
5. System reliability

The purpose is to determine whether DQE can correctly interpret natural-language questions, generate valid SQL, prevent unsafe execution, and return useful results.

## 2. Evaluation Objectives

The main evaluation objectives are:

- Measure the correctness of natural-language-to-SQL generation.
- Verify that unsafe SQL statements are rejected.
- Measure query execution latency.
- Compare query performance before and after optimization.
- Evaluate how quickly a new user can complete a basic query workflow.
- Identify failures in ingestion, validation, execution, and presentation.

## 3. Evaluation Metrics

The project defines the following success criteria.

| Metric ID | Evaluation Metric         |       Target |
| --------- | ------------------------- | -----------: |
| SC-1      | Query correctness         |       ≥ 85% |
| SC-2      | Unsafe-query rejection    |         100% |
| SC-3      | Query latency improvement |       ≥ 30% |
| SC-4      | User onboarding time      | < 60 seconds |

### 3.1 Query Correctness

Measures whether DQE generates a query that produces the expected result for a natural-language question.

Formula:

\[
\text{Accuracy} =
\frac{\text{Correct Queries}}{\text{Total Queries}}
\times 100
\]

The planned golden dataset contains 50 questions.

Target:

\[
\text{Accuracy} \geq 85\%
\]

Correctness should be determined by comparing query results with expected results, not only by checking whether SQL executes successfully.

### 3.2 SQL Safety

Measures whether unsafe SQL operations are rejected before execution.

The planned security test contains 100 test cases.

Examples include:

- DROP statements
- DELETE statements
- UPDATE statements
- INSERT statements
- Multiple SQL statements
- Malformed SQL
- Unsupported SQL constructs

Formula:

\[
\text{Rejection Rate} =
\frac{\text{Unsafe Queries Rejected}}
{\text{Total Unsafe Queries}}
\times 100
\]

Target:

\[
\text{Rejection Rate} = 100\%
\]

### 3.3 Query Performance

Measures the execution latency of queries before and after optimization.

The planned performance evaluation uses a dataset containing approximately 1 million rows.

Formula:

\[
\text{Improvement} =
\frac{T_{\text{before}}-T_{\text{after}}}
{T_{\text{before}}}
\times 100
\]

Where:

- \(T_{\text{before}}\) = execution time before optimization.
- \(T_{\text{after}}\) = execution time after optimization.

Target:

\[
\text{Improvement} \geq 30\%
\]

The benchmark should use equivalent queries, identical datasets, and comparable execution conditions.

### 3.4 User Onboarding Time

Measures the time required for a new user to complete a basic workflow.

Example workflow:

1. Open DQE.
2. Upload a dataset.
3. Ask a natural-language question.
4. View the query result.

Target:

\[
\text{Onboarding Time} < 60 \text{ seconds}
\]

## 4. Test Dataset

The evaluation uses a structured dataset with fields suitable for filtering, sorting, grouping, and aggregation.

Example dataset:

| order_id | product    | category    | quantity | revenue |
| -------: | ---------- | ----------- | -------: | ------: |
|      101 | Laptop     | Electronics |        2 |  120000 |
|      102 | Mouse      | Accessories |        5 |    5000 |
|      103 | Keyboard   | Accessories |        3 |    9000 |
|      104 | Monitor    | Electronics |        1 |   18000 |
|      105 | Headphones | Accessories |        4 |    8000 |

This table is illustrative. Actual benchmark results must use the dataset and test fixtures recorded in the experiment.

## 5. Functional Test Cases

| Test ID | Input / Action                       | Expected Result                     |
| ------- | ------------------------------------ | ----------------------------------- |
| TC-01   | Upload CSV file                      | Dataset is ingested                 |
| TC-02   | Upload JSON file                     | Dataset is ingested                 |
| TC-03   | Upload Excel file                    | Dataset is ingested                 |
| TC-04   | Upload Parquet file                  | Dataset is ingested                 |
| TC-05   | Load SQLite dataset                  | Database is accessible              |
| TC-06   | Ask for first 5 rows                 | First 5 rows are returned           |
| TC-07   | Ask for top products by revenue      | Correct aggregation and sorting     |
| TC-08   | Ask for records matching a condition | Matching records are returned       |
| TC-09   | Ask for total revenue                | Correct aggregate is returned       |
| TC-10   | Submit an invalid question           | Useful error or clarification       |
| TC-11   | Submit invalid SQL                   | Query is rejected                   |
| TC-12   | Submit a non-SELECT query            | Query is rejected                   |
| TC-13   | Request excessive output             | Result limit is enforced            |
| TC-14   | Trigger query timeout                | Execution is stopped                |
| TC-15   | Disable LLM provider                 | Supported fallback or clear failure |
| TC-16   | Request a suitable visualization     | Chart is presented where supported  |

## 6. Security Evaluation

Security testing verifies that generated SQL cannot bypass the execution policy.

### Test Categories

| Category             | Test                     | Expected Behavior |
| -------------------- | ------------------------ | ----------------- |
| Statement Validation | DROP TABLE               | Reject            |
| Statement Validation | DELETE FROM              | Reject            |
| Statement Validation | UPDATE                   | Reject            |
| Statement Validation | INSERT                   | Reject            |
| Multi-Statement      | SELECT followed by DROP  | Reject            |
| Syntax Validation    | Malformed SQL            | Reject            |
| Resource Limits      | Excessive result request | Enforce row limit |
| Execution Limits     | Long-running query       | Apply timeout     |
| Database Access      | Attempt write operation  | Deny              |

### Security Requirements

- Use read-only database connections.
- Validate SQL before execution.
- Restrict execution to permitted SELECT statements.
- Reject multiple statements.
- Apply execution timeouts.
- Enforce maximum result limits.
- Avoid exposing API keys and internal credentials.
- Treat LLM output as untrusted input.

## 7. Performance Evaluation

The performance evaluation compares the original and optimized query execution paths.

### Evaluation Procedure

1. Prepare the benchmark dataset.
2. Record the dataset size and schema.
3. Select representative queries.
4. Execute each query before optimization.
5. Record execution latency.
6. Execute the corresponding optimized query.
7. Record execution latency.
8. Compare the results for semantic equivalence.
9. Calculate the performance improvement.

### Metrics to Record

- Dataset row count
- Dataset size
- Query type
- Original SQL
- Optimized SQL
- Original execution time
- Optimized execution time
- Optimization rules applied
- Result equivalence

Performance results should include repeated measurements and report the median and relevant variation.

## 8. Reported Evaluation Results

The earlier project draft contains the following reported results:

| Metric                 | Reported Result |             Target |
| ---------------------- | --------------: | -----------------: |
| Query correctness      |     44/50 (88%) |             ≥ 85% |
| Unsafe-query rejection |  100/100 (100%) |               100% |
| Median latency         | 798 ms → 28 ms | ≥ 30% improvement |
| Latency improvement    |           96.5% |             ≥ 30% |
| Median onboarding time |      38 seconds |       < 60 seconds |

<blockquote>
**Verification status:** These values are carried forward from the earlier project draft. They should be treated as reported, not independently verified results. Before presenting them as final experimental findings, reproduce the tests and retain the test output, benchmark configuration, dataset details, and execution logs.
</blockquote>

## 9. Result Interpretation

### Query Correctness

The reported result of 44 correct queries out of 50 corresponds to 88% accuracy.

This exceeds the target of 85%, provided the golden-set evaluation is reproducible and the expected outputs are correctly defined.

### SQL Safety

The reported 100/100 unsafe-query rejection result meets the stated target.

The test suite should verify that each unsafe query is rejected before reaching the execution layer.

### Query Performance

The reported median latency decreases from 798 ms to 28 ms.

The reported improvement is approximately 96.5%.

This result should only be attributed to query optimization if both measurements isolate the relevant execution paths and use equivalent workloads. If the measurements include different stages of the pipeline, they should not be presented as a direct optimization comparison.

### User Onboarding

The reported median onboarding time is 38 seconds.

This is below the 60-second target, provided the timing procedure and participant workflow are documented.

## 10. Limitations

The evaluation has several limitations that should be considered:

- A 50-question golden set may not represent all natural-language query patterns.
- Correctness can vary with question ambiguity and schema complexity.
- Results from SQLite may not generalize to other database engines.
- LLM-generated SQL can vary across providers and model versions.
- Query performance depends on dataset structure, indexing, hardware, and cache state.
- A small onboarding test may not represent the experience of all user groups.
- Passing a fixed security test suite does not prove that every unsafe query will be rejected.

## 11. Future Evaluation Improvements

Further evaluation can include:

- Larger natural-language-to-SQL benchmark datasets.
- More complex joins and nested queries.
- Ambiguous and incomplete user questions.
- Larger datasets and different data distributions.
- Repeated performance tests under controlled conditions.
- Additional SQL injection and parser edge cases.
- Concurrent user and workload testing.
- Usability testing with a larger participant group.
- Evaluation across different LLM providers.

## 12. Conclusion

The DQE evaluation framework measures correctness, security, performance, and usability.

The project defines measurable targets and a structured testing approach. Reported results indicate progress toward these targets, but final claims should be supported by reproducible experiments and retained evidence.

A reliable evaluation process is essential for demonstrating that DQE is not only functional but also safe, accurate, and useful for structured-data querying.
