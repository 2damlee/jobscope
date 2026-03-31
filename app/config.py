import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
PROCESSED_DIR = Path(os.getenv("PROCESSED_DIR", DATA_DIR / "processed"))

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/jobscope",
)
APP_ENV = os.getenv("APP_ENV", "local")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

DB_POOL_PRE_PING = os.getenv("DB_POOL_PRE_PING", "true").lower() == "true"
DB_POOL_RECYCLE_SECONDS = int(os.getenv("DB_POOL_RECYCLE_SECONDS", "1800"))
DB_CONNECT_TIMEOUT_SECONDS = int(os.getenv("DB_CONNECT_TIMEOUT_SECONDS", "5"))

EMBEDDING_PATH = str(PROCESSED_DIR / "job_embeddings.npy")
JOB_IDS_PATH = str(PROCESSED_DIR / "job_ids.json")
CHUNK_INDEX_PATH = str(PROCESSED_DIR / "job_chunks.faiss")
CHUNK_META_PATH = str(PROCESSED_DIR / "job_chunks.json")
EMBEDDING_META_PATH = str(PROCESSED_DIR / "embedding_meta.json")
CHUNK_INDEX_META_PATH = str(PROCESSED_DIR / "chunk_index_meta.json")

RAG_USE_LLM = os.getenv("RAG_USE_LLM", "false").lower() == "true"
LLM_API_URL = os.getenv("LLM_API_URL", "")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "")
LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "20"))