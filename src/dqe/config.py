"""PS §5: Global configuration — limits, paths, dialect, LLM provider."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # loads .env from cwd or parents

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "uploads"
OUT_DIR = ROOT / "out"
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

DIALECT = "sqlite"
MAX_ROWS_RETURNED = 10_000
DEFAULT_LIMIT = 1_000
QUERY_TIMEOUT_S = 5.0
MAX_FILE_BYTES = 1_000_000_000
MAX_COLUMNS = 20

LLM_PROVIDER = os.getenv("DQE_LLM_PROVIDER", "template").lower()
XAI_API_KEY = os.getenv("XAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GROK_MODEL = os.getenv("GROK_MODEL", "grok-2-latest")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")