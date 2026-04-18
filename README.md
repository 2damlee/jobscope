# JobScope

A pipeline-oriented backend project for ingesting, processing, and serving job posting data — with embedding-based search, hybrid recommendation, and retrieval-augmented Q&A.

[![Live Demo](https://img.shields.io/badge/live-demo-brightgreen)](https://jobscope-jrur.onrender.com/docs)
[![Python](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.135-009688)](https://fastapi.tiangolo.com/)

---

## Why this project exists

Most job search tools treat search as a keyword lookup. This project explores what happens when you combine structured filtering, embedding-based similarity, and retrieval-augmented generation — and what the pipeline behind that actually looks like end-to-end.

The focus here isn't the ML itself. It's the decisions around data flow, API contract design, and making the pipeline reproducible and observable.

---

## What it does

Starting from a raw CSV of job postings, the system runs a multi-stage pipeline that produces a queryable API:

```
CSV ingestion
  → validation + normalization + deduplication (URL-keyed upsert)
  → PostgreSQL storage
  → rule-based skill extraction + text cleaning
  → sentence-transformer embeddings (FAISS index)
  → chunked document index (for retrieval)
  → FastAPI serving
```

From there, four capabilities are exposed:

- **Search** — keyword + field filter + pagination + sorting
- **Skill analytics** — frequency of detected skills by category/seniority
- **Recommendation** — hybrid scoring: embedding similarity + skill overlap + category/seniority match
- **RAG Q&A** — chunk retrieval → semantic reranking → answer generation (opt-in via `ENABLE_RAG=true`)

---

## Design decisions worth noting

**Full rebuild vs incremental.** The pipeline supports both modes. Full rebuild re-ingests everything from scratch; incremental uses URL-keyed upsert to skip already-processed records. This distinction matters when the source data changes partially — you don't want to re-embed 10k records because 200 were added.

**Why FAISS over a vector DB?** For a self-contained project without external infra dependencies, FAISS-cpu gives fast approximate nearest-neighbor search that persists to disk. A production replacement would be something like pgvector or Qdrant, but FAISS keeps this deployable with just Docker.

**Why separate embeddings and chunk indexes?** The embedding index stores one vector per job (for recommendation). The chunk index stores passage-level chunks (for retrieval). They serve different retrieval patterns and are built separately so you can rebuild one without touching the other.

**RAG as opt-in.** The `/rag/ask` endpoint is behind `ENABLE_RAG=true` because it requires the chunk index to be built and adds latency. Health endpoints (`/health/indexes`, `/health/pipeline`) let you check state before querying.

**Pipeline run tracking.** Each pipeline stage logs its run status and metadata to PostgreSQL. `/health/pipeline` surfaces this, making it possible to see what ran, when, and whether it succeeded — without external monitoring tooling.

---

## Tech stack

| Layer | Tools |
|---|---|
| API | FastAPI, Uvicorn, Pydantic |
| Storage | PostgreSQL, SQLAlchemy |
| Embeddings | SentenceTransformers, FAISS |
| Orchestration | Prefect 3.x |
| Deployment | Docker, docker-compose, Render |
| Language | Python 3.11 |

---

## Project structure

```
app/
  api/routes/       # FastAPI route handlers
  services/         # business logic layer
  models/           # SQLAlchemy ORM models
  crud/             # database access layer
  schemas/          # Pydantic request/response schemas

pipeline/
  ingest_jobs.py    # CSV ingestion + upsert
  process_jobs.py   # cleaning + skill extraction
  build_embeddings.py   # embedding index construction
  build_chunk_index.py  # chunked retrieval index
  flows.py          # Prefect flow definitions
  rebuild_all.py    # entrypoint (--full-rebuild flag)

rag/
  chunking.py       # document chunking strategy
  retriever.py      # semantic search + reranking
  qa.py             # answer generation

tests/              # unit + integration tests
data/
  raw/              # source CSVs
  processed/        # eval outputs, index artifacts
```

---

## API reference

### `GET /jobs`

List jobs with filters, pagination, and sorting.

| Param | Description |
|---|---|
| `keyword` | match title or description |
| `location` | filter by location |
| `category` | filter by category |
| `seniority` | filter by seniority |
| `page` / `size` | pagination (max 100) |
| `sort_by` | `date_posted`, `title`, `company`, etc. |
| `sort_order` | `asc` / `desc` |

### `GET /analytics/skills`

Top detected skills, filterable by `category`, `seniority`, `limit`.

### `GET /recommend/{job_id}`

Similar jobs using hybrid scoring (embedding similarity + skill overlap + category/seniority match). Scores are normalized and combined — not just vector distance.

### `POST /rag/ask`

Retrieval-augmented Q&A over job descriptions. Requires `ENABLE_RAG=true`.

```json
{
  "question": "Which backend jobs require FastAPI and PostgreSQL?",
  "category": "Backend",
  "location": "Berlin",
  "seniority": "Senior",
  "top_k": 3
}
```

### `GET /health/indexes`

Check whether embedding and chunk index artifacts exist on disk.

### `GET /health/pipeline`

Return pipeline run history — stage names, statuses, last run timestamps.

---

## Running locally

**With Docker (recommended):**

```bash
cp .env.docker.example .env.docker
docker-compose up --build
```

Then run the pipeline inside the container:

```bash
docker exec jobscope-api python -m pipeline.rebuild_all --full-rebuild
```

API will be available at `http://localhost:8000`. Interactive docs at `/docs`.

**Without Docker:**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set DATABASE_URL
python -m pipeline.rebuild_all --full-rebuild
uvicorn app.main:app --reload
```

---

## Evaluation

The pipeline includes offline evaluation scripts for both RAG and recommendation:

```bash
# RAG quality (retrieval + answer relevance)
python -m pipeline.evaluate_rag

# Recommendation quality (similarity distribution)
python -m pipeline.evaluate_recommendations
```

Results are written to `data/processed/` as JSON. This exists not to claim production-level accuracy, but to make the retrieval and scoring behavior inspectable and comparable across changes.

---

## Deployment

Deployed on Render with a managed PostgreSQL instance. The Dockerfile handles both `wait_for_db` (startup probe) and the API process. A production-specific compose file (`docker-compose.prod.yml`) handles environment separation.

Live: [https://jobscope-jrur.onrender.com/docs](https://jobscope-jrur.onrender.com/docs)

---

## Limitations and what's next

This project uses a static CSV as the data source. A more realistic version would pull from a live job board API or a scheduled scraper, which would make the incremental pipeline logic more meaningful in practice.

The RAG component uses a simple chunking strategy and doesn't tune retrieval parameters per query type. Reranking is based on semantic similarity; a cross-encoder reranker would likely improve precision for longer questions.

Potential next steps: swap FAISS for pgvector to simplify the deployment surface, add query logging to make evaluation continuous rather than batch, and expose the pipeline run health more prominently in the API response format.