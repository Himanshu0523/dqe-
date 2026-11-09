"""Four-panel UI: Input → Preview → Ask → Results. Wraps the existing dqe pipeline."""
from __future__ import annotations
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import pandas as pd
import streamlit as st

from dqe import config
from dqe.contracts import Schema
from dqe.ingest import registry
from dqe.store.sqlite_store import SQLiteStore
from dqe.store import indexer
from dqe.nl2query.translator import get_translator, TemplateTranslator, _LLMTranslator
from dqe.query import validator, optimizer, explain
from dqe.execute import executor
from dqe.present import table_view, summary
from web.state import init, reset
from web.voice import speech_input, speak

st.set_page_config(page_title="Dataset Query Engine", page_icon="🔎", layout="wide")
init(st)

#  header 
st.markdown("## 🔎 Dataset Query Engine")
st.caption("Upload → Preview → Ask (type or speak) → Results")

@st.cache_resource(show_spinner=False)
def cached_translator(provider: str):
    from dqe.nl2query.translator import get_translator
    return get_translator(provider)


@st.cache_data(show_spinner=False, ttl=600)
def cached_explain(db_path: str, sql: str) -> str:
    from dqe.store.sqlite_store import SQLiteStore
    return SQLiteStore(Path(db_path)).explain(sql)

# step indicator
step = st.session_state.step
c1, c2, c3, c4 = st.columns(4)
for i, (col, label) in enumerate(
    [(c1, "1 · Input"), (c2, "2 · Data"), (c3, "3 · Ask"), (c4, "4 · Results")],
    start=1,
):
    with col:
        active = i == step
        st.markdown(
            f"<div style='padding:10px;border-radius:8px;text-align:center;"
            f"background:{'#0b5fff' if active else '#f0f0f0'};"
            f"color:{'#fff' if active else '#333'};font-weight:600'>{label}</div>",
            unsafe_allow_html=True,
        )

st.divider()

#  PANEL 1 — INPUT 
if step == 1:
    st.subheader("1 · Upload a dataset")
    st.write("Supported: `.csv`, `.json`, `.jsonl`, `.xlsx`, `.parquet`, `.db`, `.sqlite`")

    uploaded = st.file_uploader(
        "Drop your file here",
        type=["csv", "json", "jsonl", "xlsx", "xls", "parquet", "db", "sqlite", "sqlite3"],
    )

    if uploaded:
        tmp = config.DATA_DIR / uploaded.name
        tmp.write_bytes(uploaded.getbuffer())

        with st.spinner("Loading, inferring schema, indexing..."):
            try:
                df, schema = registry.load_file(tmp)
                store = SQLiteStore(config.DATA_DIR / f"{schema.table_name}.sqlite")
                store.create_table(df, schema)
                indexed = indexer.auto_index(store, df, schema)

                st.session_state.df = df
                st.session_state.schema = schema
                st.session_state.store = store

                st.success(
                    f"Loaded **{schema.table_name}** — "
                    f"{schema.row_count} rows × {len(schema.columns)} columns"
                )
                if indexed:
                    st.info(f"Indexed: {', '.join(indexed)}")

                if st.button("Continue → Preview data", type="primary"):
                    st.session_state.step = 2
                    st.rerun()
            except Exception as e:
                st.error(f"Load failed: {e}")

# ================== PANEL 2 — PREVIEW DATA ==================
elif step == 2:
    st.subheader("2 · Preview data")
    df: pd.DataFrame = st.session_state.df
    schema: Schema = st.session_state.schema

    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.markdown(f"**{schema.table_name}** — first 50 rows")
        st.dataframe(df.head(50), width="stretch")
    with col_b:
        st.markdown("**Schema**")
        for c in schema.columns:
            null = "NULL" if c.nullable else "NOT NULL"
            pk = " 🔑" if c.name == schema.primary_key else ""
            st.markdown(f"- `{c.name}` · {c.dtype} · {null}{pk}")
        if schema.indexed_columns:
            st.markdown(f"**Indexed:** {', '.join(schema.indexed_columns)}")

    st.divider()
    b1, b2 = st.columns(2)
    with b1:
        if st.button("← Back to upload"):
            reset(st)
            st.rerun()
    with b2:
        if st.button("Continue → Ask a question", type="primary"):
            st.session_state.step = 3
            st.rerun()

#  PANEL 3 — ASK 
elif step == 3:
    st.subheader("3 · Ask your question")
    schemas = [st.session_state.schema]

    provider = st.radio(
        "Translation engine",
        ["gemini", "grok", "openai", "template"],
        horizontal=True,
        index=0,
        key="provider_radio",
    )

    with st.form("ask_form", clear_on_submit=False):
        typed = st.text_area(
            "Question",
            placeholder="e.g. which categories earned the most, and what was the average per category?",
            height=90,
            label_visibility="collapsed",
        )
        with st.expander("🎙️ Or speak your question"):
            st.write("Click **Speak**, say your question, copy the transcript into the box above.")
            speech_input("mic1")
            st.caption("Browser speech runs locally; nothing is uploaded.")
        submitted = st.form_submit_button("Run query", type="primary")

    if submitted and typed.strip():
        question = typed.strip()
        st.session_state.question = question
        st.session_state.provider = provider

        with st.spinner(f"Translating via {provider}..."):
            try:
                if provider == "template":
                    sql = TemplateTranslator().to_sql(question, schemas, config.DIALECT)
                else:
                    tr = cached_translator(provider)
                    if not isinstance(tr, _LLMTranslator):
                        raise RuntimeError(f"{provider} unavailable — check API key in .env")
                    sql = tr.to_sql_with_retry(
                        question, schemas, config.DIALECT,
                        lambda s: validator.validate(s, schemas, config.DIALECT),
                    )
                st.session_state.sql = sql
            except Exception as e:
                st.error(f"Translation failed: {e}")
                st.stop()

        v = validator.validate(st.session_state.sql, schemas, config.DIALECT)
        if not v.ok:
            st.error(f"Rejected: {v.reason}\n\nAttempted SQL:\n```sql\n{v.sql}\n```")
            st.stop()

        opt = optimizer.optimize(v.sql, schemas, config.DIALECT)
        rs = executor.execute(st.session_state.store, opt.sql)

        st.session_state.opt = opt
        st.session_state.result = rs
        st.session_state.step = 4
        st.rerun()

    if st.button("← Back to data"):
        st.session_state.step = 2
        st.rerun()#  PANEL 4 — RESULTS 
        
        
elif step == 4:
    st.subheader("4 · Results")
    rs = st.session_state.result
    opt = st.session_state.opt
    store = st.session_state.store

    if rs.error:
        st.error(f"Execution failed: {rs.error}")
    else:
        st.markdown(f"**Question:** _{st.session_state.question}_")

        st.markdown("**SQL that ran**")
        st.code(opt.sql, language="sql")

        if opt.changes:
            st.markdown("**Optimizations applied**")
            for ch in opt.changes:
                st.markdown(f"- {ch}")

        with st.expander("Execution plan (before / after)"):
            st.text("Original:\n" + store.explain(st.session_state.sql))
            st.text("\nOptimized:\n" + store.explain(opt.sql))

        st.markdown(f"**Result — {rs.row_count} row(s) in {rs.elapsed_ms} ms**")
        df_res = pd.DataFrame(rs.rows, columns=rs.columns)
        st.dataframe(df_res, width="stretch", height=360)

        if rs.truncated:
            st.warning(f"Result truncated at {config.MAX_ROWS_RETURNED} rows.")

        summary_text = (
            f"Query returned {rs.row_count} rows in {rs.elapsed_ms:.1f} milliseconds."
        )
        if st.button("🔊 Speak summary"):
            speak(summary_text)

        csv = df_res.to_csv(index=False).encode("utf-8")
        st.download_button("⬇ Download results as CSV", csv,
                           file_name=f"{st.session_state.schema.table_name}_results.csv",
                           mime="text/csv")

    st.divider()
    b1, b2 = st.columns(2)
    with b1:
        if st.button("← Ask another question"):
            st.session_state.step = 3
            st.session_state.result = None
            st.session_state.opt = None
            st.rerun()
    with b2:
        if st.button("↺ Start over"):
            reset(st)
            st.rerun()


