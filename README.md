# JobScope

A pipeline-oriented backend project for ingesting, processing, and serving job posting data — with embedding-based recommendation, hybrid scoring, and retrieval-augmented Q&A.

[![Live Demo](https://img.shields.io/badge/live-demo-brightgreen)](https://jobscope-jrur.onrender.com/docs)
[![Python](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/)
[![CI](https://github.com/2damlee/jobscope/actions/workflows/ci.yml/badge.svg)](https://github.com/2damlee/jobscope/actions/workflows/ci.yml)

---

## What this is

Starting from real tech job postings (sourced from the LinkedIn public dataset on Kaggle), the system runs a multi-stage pipeline that builds a queryable API with search, recommendation, analytics, and optional RAG-based Q&A.

The engineering focus is on the pipeline design: how data flows from ingestion to serving, how changes propagate downstream, and how the system behaves when artifacts are unavailable.

```
LinkedIn job postings CSV (Kaggle public dataset, tech roles)
  → title-based categorization + seniority normalization
  → validation + normalization + URL-keyed upsert
  → PostgreSQL (schema managed by Alembic)
  → rule-based skill extraction (60+ patterns)
  → sentence-transformer embeddings, all-MiniLM-L6-v2 (FAISS index)
  → chunked document index (for RAG retrieval)
  → FastAPI serving
```



**2. Startup-time artifact caching with graceful degradation**

Embedding artifacts are loaded into `app.state` once at startup via FastAPI's `lifespan` handler. Every recommendation request reads from memory using a single dot-product operation — no disk I/O per request. If artifacts are missing at startup, recommendation and RAG endpoints return `503 Service Unavailable` rather than crashing. `/health/ready` reflects full readiness state including artifact availability and database reachability.

**3. Pipeline observability via run tracking**

Every pipeline stage records its execution — rows processed, duration in seconds, inserted/updated/skipped counts, error messages — into a `pipeline_runs` table. The `/health/pipeline` endpoint exposes the last 10 runs, making it possible to audit pipeline state without external monitoring tooling.

---

## Tech stack

| Layer | Tools |
|---|---|
| API | FastAPI, Uvicorn, Pydantic v2 |
| Storage | PostgreSQL, SQLAlchemy 2.x |
| Migrations | Alembic |
| Embeddings | SentenceTransformers (`all-MiniLM-L6-v2`), FAISS |
| Orchestration | Prefect 3.x |
| Deployment | Docker, docker-compose, Render |
| Language | Python 3.11 |

---

## Project structure

```
app/
  api/              # route handlers — jobs, recommend, analytics, health, rag
  services/         # business logic + input normalization
  crud.py           # database query layer (PostgreSQL unnest for skill aggregation)
  models.py         # SQLAlchemy ORM models
  schemas.py        # Pydantic request/response schemas
  artifacts.py      # artifact readiness check
  time_utils.py     # timezone-safe datetime helper

pipeline/
  ingest_jobs.py        # CSV ingestion, SHA-256 hash-based upsert, downstream reset
  process_jobs.py       # text cleaning + rule-based skill extraction
  build_embeddings.py   # FAISS embedding index, updates embedded_at per job
  build_chunk_index.py  # chunked retrieval index, updates chunked_at per job
  flows.py              # Prefect task and flow definitions
  rebuild_all.py        # CLI entrypoint (--full-rebuild flag)
  run_tracker.py        # pipeline run recording to DB
  state_utils.py        # SHA-256 source hash computation
  skill_dict.py         # 60+ skill extraction patterns

rag/
  chunking.py           # sentence-based chunking with overlap
  retriever.py          # FAISS search + keyword overlap scoring
  qa.py                 # reranking, deduplication, answer dispatch
  answer_generation.py  # extractive answer generation
  llm_client.py         # optional LLM backend (OpenAI-compatible)

alembic/
  env.py                # reads DATABASE_URL from environment
  versions/             # migration history (initial_schema committed)

scripts/
  prepare_kaggle_jobs.py  # transforms Kaggle LinkedIn dataset to pipeline schema

tests/
  conftest.py                    # SQLite integration fixtures
  test_api_integration.py        # end-to-end API tests
  test_postgres_integration.py   # Postgres-specific integration tests
  test_*.py                      # unit tests per module
```

---

## Data

The dataset is sourced from the [LinkedIn Job Postings dataset on Kaggle](https://www.kaggle.com/datasets/arshkon/linkedin-job-postings). `scripts/prepare_kaggle_jobs.py` transforms it into the pipeline schema: title-based category classification (software engineering / data engineering / machine learning), seniority normalization, description cleaning, and deduplication by URL.

The script uses title-only classification intentionally — description-based matching causes false positives (e.g., `"enrollment"` matching the `"llm"` pattern). Non-tech postings are excluded before any row limit is applied.

To regenerate the dataset from a Kaggle download:

```bash
# With full Kaggle dataset (~124k rows → clean 500 tech jobs)
python scripts/prepare_kaggle_jobs.py \
  --external-dir data/external \
  --max-rows 500

# With the 800-row sample included in the repo
python scripts/prepare_kaggle_jobs.py \
  --external-dir data/external \
  --max-rows 350
```

---

## Recommendation scoring

`/recommend/{job_id}` uses a hybrid scoring function rather than raw vector distance:

```
final_score = 0.70 × embedding_similarity
            + 0.20 × skill_overlap (Jaccard)
            + 0.07 × category_match
            + 0.03 × seniority_match
```

Embedding similarity alone can surface structurally similar but domain-unrelated jobs. Skill overlap and category bonuses anchor results to domain-relevant matches. Each recommendation result includes `company`, `location`, `url`, `category`, and `seniority` so consumers can navigate to the original posting without a separate lookup.

---

## API reference

### `GET /jobs`

List jobs with keyword search, field filters, skill filter, pagination, and sorting.

| Param | Description |
|---|---|
| `keyword` | match title, description, or cleaned description |
| `location` | filter by location (partial match) |
| `category` | filter by category |
| `seniority` | filter by seniority |
| `skills` | comma-separated skill names, e.g. `python,sql,dbt` |
| `page` / `size` | pagination (max 100 per page) |
| `sort_by` | `date_posted`, `title`, `company`, `location`, `category`, `seniority` |
| `sort_order` | `asc` / `desc` |

### `GET /jobs/{job_id}`

Single job detail by ID.

### `GET /analytics/skills`

Top detected skills aggregated via PostgreSQL `unnest` on the `detected_skills` column, filterable by `category`, `seniority`, `limit` (max 50).

### `GET /recommend/{job_id}`

Similar jobs ranked by hybrid score. Response includes score breakdown, shared skills, and direct URL to the original posting.

Optional filters:
- `same_category_only` — restrict candidates to same category
- `min_shared_skills` — minimum required shared detected skills (0–10)
- `min_embedding_score` — cosine similarity floor for candidates (-1.0 to 1.0)

### `POST /rag/ask`

Retrieval-augmented Q&A over job descriptions. Enabled via `ENABLE_RAG=true`.

```json
{
  "question": "Which backend jobs require FastAPI and PostgreSQL?",
  "category": "software engineering",
  "location": "New York",
  "seniority": "senior",
  "top_k": 3
}
```

### `GET /health/ready`

Full readiness check: database + artifact files + embedding cache in memory. Returns `503` when degraded.

### `GET /health/indexes`

Artifact metadata: model name, job count, generation timestamp, staleness (stale after 24h).

### `GET /health/pipeline`

Last 10 pipeline run records: stage name, status, row counts, duration, error detail.

### `GET /health/db`

Database connectivity check.

---

## Running locally

**With Docker (recommended):**

```bash
cp .env.docker.example .env.docker
docker-compose up --build
```

Run the pipeline inside the container:

```bash
docker exec jobscope-api python -m pipeline.rebuild_all --full-rebuild
```

API at `http://localhost:8000`, docs at `/docs`.

**Without Docker:**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set DATABASE_URL

alembic upgrade head
python -m pipeline.rebuild_all --full-rebuild
uvicorn app.main:app --reload
```

---

## Pipeline modes

```bash
# Full rebuild — re-ingests all records, resets all downstream state
python -m pipeline.rebuild_all --full-rebuild

# Incremental — processes only changed records (hash-based)
python -m pipeline.rebuild_all
```

In incremental mode, each record's SHA-256 hash is compared to the stored value. Unchanged records — and their downstream artifacts — are skipped. Changed records have `processing_status`, `embedded_at`, and `chunked_at` reset, triggering selective reprocessing.

---

## Schema migrations

Alembic manages the schema. Migration files are tracked in `alembic/versions/`.

```bash
# Apply all pending migrations (runs automatically on Docker startup)
alembic upgrade head

# Generate a migration after changing models.py
alembic revision --autogenerate -m "description"

# Check current revision
alembic current
```

---

## Evaluation

```bash
# RAG retrieval quality (keyword hit rate over eval cases)
python -m pipeline.evaluate_rag

# Recommendation quality (shared skill coverage)
python -m pipeline.evaluate_recommendations
```

Results written to `data/processed/` as JSON. These are offline sanity checks, not production metrics.

---

## Deployment

Deployed on Render with a managed PostgreSQL instance. On each container startup, `alembic upgrade head` applies any pending migrations before the API starts.

Live: [https://jobscope-jrur.onrender.com/docs](https://jobscope-jrur.onrender.com/docs)

`docker-compose.prod.yml` is provided for self-hosted production use.

---

## Limitations and what's next

The data source is a static CSV snapshot from Kaggle. A natural extension is connecting the pipeline to a live API — the Bundesagentur für Arbeit (German Federal Employment Agency) provides a free public REST API that would make the incremental pipeline logic meaningful with continuously updated data.

`detected_skills` is stored as a comma-separated text column. Migrating to a PostgreSQL array type or a normalized `job_skills` junction table would enable more efficient joins and filtering at the DB level.

The RAG reranking combines FAISS cosine similarity with token overlap. A cross-encoder reranker would improve precision for longer or more specific questions.

Rate limiting and authentication are not implemented. The architecture supports adding FastAPI middleware for both without structural changes.