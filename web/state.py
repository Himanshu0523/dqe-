"""Session keys shared across panels. Import once, use everywhere."""
KEYS = {
    "step": 1,                # current panel: 1|2|3|4
    "df": None,               # pandas DataFrame
    "schema": None,           # dqe.contracts.Schema
    "store": None,            # SQLiteStore
    "question": "",           # last user question (typed or spoken)
    "sql": "",                # generated SQL
    "opt": None,              # OptimizedQuery
    "result": None,           # ResultSet
    "provider": "gemini",     # grok|gemini|openai|template
    "error": None,            # last error string
}


def init(st) -> None:
    for k, v in KEYS.items():
        if k not in st.session_state:
            st.session_state[k] = v


def reset(st) -> None:
    for k, v in KEYS.items():
        st.session_state[k] = v