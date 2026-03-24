import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/jobscope")
APP_ENV = os.getenv("APP_ENV", "local")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

EMBEDDING_PATH = "data/processed/job_embeddings.npy"
JOB_IDS_PATH = "data/processed/job_ids.json"
CHUNK_INDEX_PATH = "data/processed/job_chunks.faiss"
CHUNK_META_PATH = "data/processed/job_chunks.json"
EMBEDDING_META_PATH = "data/processed/embedding_meta.json"
CHUNK_INDEX_META_PATH = "data/processed/chunk_index_meta.json"

RAG_USE_LLM = os.getenv("RAG_USE_LLM", "false").lower() == "true"
LLM_API_URL = os.getenv("LLM_API_URL", "")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "")
LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "20"))