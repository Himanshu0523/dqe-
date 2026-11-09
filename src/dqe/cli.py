"""PS §3: pipeline — translate (LLM first), validate, optimize, execute, present."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

from rich.console import Console

from dqe import config
from dqe.ingest import registry
from dqe.store import catalog, indexer
from dqe.store.sqlite_store import SQLiteStore
from dqe.nl2query.translator import (
    TemplateTranslator, _LLMTranslator, get_translator,
)
from dqe.query import validator, optimizer, explain
from dqe.execute import executor
from dqe.present import table_view, chart, summary

console = Console()


def _db_path_for(table: str) -> Path:
    return config.DATA_DIR / f"{table}.sqlite"


def cmd_upload(args) -> int:
    path = Path(args.file)
    console.print(f"[bold]Loading[/bold] {path.name} ...")
    df, schema = registry.load_file(path)
    store = SQLiteStore(_db_path_for(schema.table_name))
    store.create_table(df, schema)
    indexed = indexer.auto_index(store, df, schema)
    catalog.register(schema)
    console.print(
        f"[green]✓[/green] Loaded [bold]{schema.table_name}[/bold]: "
        f"{schema.row_count} rows, {len(schema.columns)} columns"
    )
    if indexed:
        console.print(f"  indexed: {', '.join(indexed)}")
    console.print(f"  db: {store.db_path}")
    console.print(f"  Try: dqe ask {schema.table_name} \"your question here\"")
    return 0


def _translate(question: str, provider: str | None) -> tuple[str, list]:
    """PS §3: LLM first with validator-feedback retry; template as offline fallback."""
    schemas = catalog.all_schemas()
    if not schemas:
        raise RuntimeError("No tables loaded. Run 'dqe upload <file>' first.")

    def _validate(sql: str):
        return validator.validate(sql, schemas, config.DIALECT)

    if provider and provider != "template":
        try:
            tr = get_translator(provider)
            if isinstance(tr, _LLMTranslator):
                sql = tr.to_sql_with_retry(question, schemas, config.DIALECT, _validate)
            else:
                sql = tr.to_sql(question, schemas, config.DIALECT)
            return sql, schemas
        except Exception as e:
            console.print(f"[yellow]LLM translation failed: {e}[/yellow]")
            console.print("[yellow]Trying template fallback...[/yellow]")

    try:
        return TemplateTranslator().to_sql(question, schemas, config.DIALECT), schemas
    except Exception as e:
        raise RuntimeError(
            f"Could not translate question. {e}\n"
            f"Tip: rephrase as 'top N by X', 'count by X', 'average X', "
            f"or pass --provider grok/gemini for free-form questions."
        )


def run_pipeline(question: str, provider: str | None = None,
                 raw_sql: bool = False) -> int:
    if raw_sql:
        sql = question
        schemas = catalog.all_schemas()
        if not schemas:
            console.print("[red]No tables loaded. Run 'dqe upload <file>' first.[/red]")
            return 1
    else:
        try:
            sql, schemas = _translate(question, provider)
        except Exception as e:
            console.print(f"[red]Translation failed:[/red] {e}")
            return 2

    v = validator.validate(sql, schemas, config.DIALECT)
    if not v.ok:
        console.print(f"[red]Rejected:[/red] {v.reason}")
        console.print(f"  attempted SQL: {sql}")
        return 3

    opt = optimizer.optimize(v.sql, schemas, config.DIALECT)

    primary = schemas[0]
    store = SQLiteStore(_db_path_for(primary.table_name))

    rs = executor.execute(store, opt.sql)
    if rs.error:
        table_view.render(rs)
        return 4

    console.rule(f"[bold cyan]{question}[/bold cyan]")
    console.print(f"[bold]SQL:[/bold] {opt.sql}")
    console.print(f"[bold]Changes:[/bold] {', '.join(opt.changes) if opt.changes else '(none)'}")
    try:
        console.print(explain.render(v.sql, opt, store.explain(v.sql), store.explain(opt.sql)))
    except Exception:
        pass
    table_view.render(rs)
    console.print(summary.one_liner(rs))
    img = chart.maybe_chart(rs, name="chart")
    if img:
        console.print(f"  chart: {img}")
    return 0


def cmd_query(args) -> int:
    return run_pipeline(args.sql, raw_sql=True)


def cmd_ask(args) -> int:
    return run_pipeline(args.question, provider=args.provider)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="dqe", description="Universal Dataset Query Engine")
    sub = p.add_subparsers(dest="cmd", required=True)

    up = sub.add_parser("upload", help="Load a dataset")
    up.add_argument("file")
    up.set_defaults(fn=cmd_upload)

    q = sub.add_parser("query", help="Run raw SQL")
    q.add_argument("sql")
    q.set_defaults(fn=cmd_query)

    a = sub.add_parser("ask", help="Ask a question in English")
    a.add_argument("question")
    a.add_argument("--provider", choices=["grok", "gemini", "openai", "template"],
                   default=None)
    a.set_defaults(fn=cmd_ask)

    args = p.parse_args(argv)
    catalog.hydrate()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())