# JobScope

JobScope is a pipeline-oriented backend and data engineering project for ingesting, processing, indexing, and serving job posting data.

It is built to show an end-to-end workflow across data ingestion, transformation, retrieval, recommendation, and API serving.

## Overview

Core flow:

```text
CSV ingestion -> PostgreSQL -> cleaning / skill extraction -> embeddings / chunk index -> FastAPI APIs
```

The project focuses on two areas:

- pipeline-oriented data processing
- API-based serving for search, analytics, recommendation, and retrieval

---

## 🔗 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Pipeline](#pipeline)
- [API](#api)
- [Running Locally](#running-locally)
- [Running with Docker](#running-with-docker)

---

## Features

- CSV ingestion with validation, normalization, and URL-based upsert
- PostgreSQL-backed storage
- Cleaning and rule-based skill extraction
- Hybrid recommendation using embeddings and structured metadata
- Retrieval-based Q&A with chunking, semantic retrieval, reranking, and deduplication
- Pipeline run tracking and health checks
- Prefect flow wrapper for pipeline orchestration
- Docker-based local development

---

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Pandas
- sentence-transformers
- FAISS
- Prefect
- Docker

---

## Architecture

```text
Source CSV
  -> ingest and validate
  -> store in PostgreSQL
  -> clean descriptions and extract skills
  -> build job embeddings and chunk index
  -> serve APIs for jobs, analytics, recommendation, and RAG
```

---

## Project Structure

```text
jobscope/
├── app/
│   ├── api/
│   ├── config.py
│   ├── crud.py
│   ├── db.py
│   ├── logging.py
│   ├── main.py
│   ├── middleware.py
│   ├── models.py
│   ├── recommendation.py
│   └── schemas.py
├── pipeline/
│   ├── build_chunk_index.py
│   ├── build_embeddings.py
│   ├── clean_jobs.py
│   ├── create_tables.py
│   ├── evaluate_rag.py
│   ├── extract_skills.py
│   ├── flows.py
│   ├── ingest_jobs.py
│   ├── process_jobs.py
│   ├── rebuild_all.py
│   ├── rebuild_utils.py
│   ├── run_tracker.py
│   ├── skill_dict.py
│   └── state_utils.py
├── rag/
├── tests/
├── data/
│   ├── raw/
│   └── processed/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Pipeline

### 1. Ingestion

- reads `data/raw/jobs.csv`
- validates required fields
- normalizes selected fields
- upserts into PostgreSQL by URL

---

### 2. Processing

- cleans descriptions
- extracts skills using a rule-based taxonomy and alias mapping
- stores processed text for downstream use

---

### 3. Embeddings and Indexing

- builds job-level embeddings for recommendation
- builds chunk-level embeddings and FAISS index for retrieval
- stores generated artifacts in `data/processed/`

---

### 4. Recommendation

Hybrid recommendation combines:

- embedding similarity
- skill overlap
- category match
- seniority match

---

### 5. Retrieval / RAG

RAG flow includes:

- sentence-aware chunking
- semantic retrieval
- keyword reranking
- source deduplication
- optional LLM synthesis with extractive fallback

---

### 6. Operations

- `pipeline_runs` stores pipeline execution metadata
- `/health/indexes` returns artifact metadata
- `/health/pipeline` returns recent pipeline run summaries
- `pipeline/flows.py` defines the Prefect flow
- `pipeline/rebuild_all.py` runs the pipeline stages in sequence for local execution

---

## API

### GET /jobs

Returns job listings with filter support.

Example:

```text
GET /jobs?location=Berlin&category=Data%20Engineering
```

---

### GET /analytics/skills

Returns skill frequency analytics.

```text
GET /analytics/skills?location=Berlin
```

---

### GET /recommend/{job_id}

Returns similar jobs using hybrid recommendation scoring.

```text
GET /recommend/1?limit=5&same_category_only=true
```

---

### POST /rag/ask

Answers questions over indexed job descriptions.

```json
{
  "question": "Which backend jobs require FastAPI and PostgreSQL?",
  "top_k": 3
}
```

---

### GET /health/indexes

Returns embedding and chunk index metadata.

---

### GET /health/pipeline

Returns recent pipeline run summaries.

---

## Running Locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python pipeline/create_tables.py
uvicorn app.main:app --reload
```

Docs:

http://127.0.0.1:8000/docs

---

## Running with Docker

```bash
docker compose up --build
docker compose exec api python -m pipeline.rebuild_all
```

---

## Notes

This project keeps the retrieval and recommendation layer lightweight and interview-friendly.

The current vector artifacts are file-based. A natural next step is to extend the incremental pipeline further or move vector storage into PostgreSQL with pgvector or a dedicated vector store.