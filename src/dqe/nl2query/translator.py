"""PS §3: General NL→SQL. LLM primary; template fallback; validated retry loop."""
from __future__ import annotations
import json
import re
import sys
import time
from typing import Protocol

from dqe import config
from dqe.contracts import Schema
from dqe.nl2query.prompts import SYSTEM_PROMPT, RETRY_PROMPT
from dqe.nl2query.schema_context import build_context


class Translator(Protocol):
    def to_sql(self, question: str, schemas: list[Schema], dialect: str) -> str: ...


#  template
class TemplateTranslator:
    """Offline fallback: covers simple intents. Not the primary path."""

    def to_sql(self, question: str, schemas: list[Schema], dialect: str) -> str:
        if not schemas:
            raise ValueError("No tables loaded")
        q = question.lower().strip()
        s = schemas[0]
        t = s.table_name
        cols = s.column_names()

        if any(k in q for k in ("how many", "count rows", "number of rows")):
            return f'SELECT COUNT(*) AS n FROM "{t}"'

        m = re.search(r"top\s+(\d+).*?(?:by|of|for)\s+([a-z_][a-z0-9_]*)", q)
        if m and m.group(2) in cols:
            return f'SELECT * FROM "{t}" ORDER BY "{m.group(2)}" DESC LIMIT {m.group(1)}'

        m = re.search(r"(?:average|avg|mean)\s+(?:of\s+)?([a-z_][a-z0-9_]*)", q)
        if m and m.group(1) in cols:
            c = m.group(1)
            return f'SELECT AVG("{c}") AS avg_{c} FROM "{t}"'

        m = re.search(r"(?:count|group)\s+(?:.*?\s+)?by\s+([a-z_][a-z0-9_]*)", q)
        if m and m.group(1) in cols:
            c = m.group(1)
            return f'SELECT "{c}", COUNT(*) AS n FROM "{t}" GROUP BY "{c}" ORDER BY n DESC'

        m = re.search(
            r"where\s+([a-z_][a-z0-9_]*)\s*(=|>|<|>=|<=|!=)\s*['\"]?([\w\.\-]+)['\"]?", q
        )
        if m and m.group(1) in cols:
            c, op, v = m.group(1), m.group(2), m.group(3)
            return f'SELECT * FROM "{t}" WHERE "{c}" {op} \'{v}\''

        if any(k in q for k in ("show", "list", "all", "display", "rows")):
            return f'SELECT * FROM "{t}"'

        raise ValueError(
            "TemplateTranslator only handles simple phrasing. "
            "Use --provider grok/gemini for free-form questions."
        )


import time

class _LLMTranslator:
    """Shared prompt → parse → validate-retry loop, with transient-error retry."""

    MAX_TRANSIENT_RETRIES = 3
    BACKOFF_BASE_S = 1.5

    def _raw_call(self, system: str, user: str) -> str:
        raise NotImplementedError

    def _raw_call_with_retry(self, system: str, user: str) -> str:
        last_exc: Exception | None = None
        for attempt in range(self.MAX_TRANSIENT_RETRIES):
            try:
                return self._raw_call(system, user)
            except Exception as e:
                msg = str(e).lower()
                transient = any(k in msg for k in (
                    "503", "unavailable", "high demand", "timeout",
                    "temporarily", "overloaded", "rate limit", "429",
                    "resource exhausted",
                ))
                last_exc = e
                if not transient or attempt == self.MAX_TRANSIENT_RETRIES - 1:
                    raise
                wait = self.BACKOFF_BASE_S * (2 ** attempt)
                print(f"[dqe] LLM transient error ({type(e).__name__}); "
                      f"retrying in {wait:.1f}s (attempt {attempt+2}/{self.MAX_TRANSIENT_RETRIES})",
                      file=sys.stderr)
                time.sleep(wait)
        raise last_exc  # unreachable
    
    

    def to_sql_with_retry(self, question, schemas, dialect, validate_fn, max_attempts=2):
        ctx = build_context(schemas)
        base = f"{ctx}\n\nQuestion: {question}\n\nReturn JSON: {{\"sql\": \"...\"}}"
        last_sql, last_err = "", ""
        for attempt in range(max_attempts):
            user = base if attempt == 0 else base + "\n\n" + RETRY_PROMPT.format(
                error=last_err, sql=last_sql)
            raw = self._raw_call_with_retry(SYSTEM_PROMPT, user)
            last_sql = self._extract_sql(raw)
            if not last_sql:
                last_err = "empty SQL"
                continue
            vr = validate_fn(last_sql)
            if vr.ok:
                return last_sql
            last_err = vr.reason or "validation failed"
        raise ValueError(f"LLM could not produce valid SQL after {max_attempts} attempts: {last_err}")
# ------------------------------------------------------------------ providers
class GrokTranslator(_LLMTranslator):
    def __init__(self, model: str | None = None, api_key: str | None = None):
        from openai import OpenAI
        key = api_key or config.XAI_API_KEY
        if not key:
            raise RuntimeError("XAI_API_KEY not set")
        self.client = OpenAI(api_key=key, base_url="https://api.x.ai/v1")
        self.model = model or config.GROK_MODEL

    def _raw_call(self, system: str, user: str) -> str:
        r = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            temperature=0,
        )
        return r.choices[0].message.content or ""


class GeminiTranslator(_LLMTranslator):
    def __init__(self, model: str | None = None, api_key: str | None = None):
        from google import genai
        key = api_key or config.GEMINI_API_KEY
        if not key:
            raise RuntimeError("GEMINI_API_KEY not set")
        self.client = genai.Client(api_key=key)
        self.model = model or config.GEMINI_MODEL

    def _raw_call(self, system: str, user: str) -> str:
        r = self.client.models.generate_content(
            model=self.model, contents=f"{system}\n\n{user}"
        )
        return getattr(r, "text", "") or ""


class OpenAITranslator(_LLMTranslator):
    def __init__(self, model: str | None = None, api_key: str | None = None):
        from openai import OpenAI
        key = api_key or config.OPENAI_API_KEY
        if not key:
            raise RuntimeError("OPENAI_API_KEY not set")
        self.client = OpenAI(api_key=key)
        self.model = model or config.OPENAI_MODEL

    def _raw_call(self, system: str, user: str) -> str:
        r = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            response_format={"type": "json_object"},
            temperature=0,
        )
        return r.choices[0].message.content or ""


# ------------------------------------------------------------------ factory
def get_translator(provider: str | None = None) -> Translator:
    """PS §3/§5: pick translator; fall back to template if key missing or SDK absent."""
    provider = (provider or config.LLM_PROVIDER).lower()
    try:
        if provider == "grok":
            return GrokTranslator()
        if provider == "gemini":
            return GeminiTranslator()
        if provider == "openai":
            return OpenAITranslator()
    except Exception as e:
        print(f"[dqe] {provider} unavailable ({e}); falling back to template",
              file=sys.stderr)
    return TemplateTranslator()