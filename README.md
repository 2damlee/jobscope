# JobScope

JobScope is a pipeline-oriented backend and data engineering project for ingesting, processing, indexing, and serving job posting data.

It is built to show an end-to-end workflow across data ingestion, transformation, retrieval, recommendation, and API serving.

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

## Overview

Core flow:

```
CSV ingestion → PostgreSQL → cleaning / skill extraction → embeddings → indexing → FastAPI
```

---

## Features

- CSV ingestion with validation, normalization, and URL-based upsert
- PostgreSQL-backed storage
- Cleaning and rule-based skill extraction
- Hybrid recommendation using embeddings and structured metadata
- Retrieval-based Q&A with chunking, semantic retrieval, reranking, and deduplication
- Pipeline run tracking and health checks
- Prefect-based pipeline orchestration
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

```
Source CSV
 → ingestion & validation
 → PostgreSQL
 → cleaning & skill extraction
 → job embeddings / chunk embeddings
 → FAISS indexes
 → FastAPI APIs (jobs / analytics / recommend / rag)
```

---

## Project Structure

```text
jobscope/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── db.py
│   ├── models.py
│   ├── schemas.py
│   ├── crud.py
│   ├── filters.py
│   ├── recommendation.py
│   ├── logging.py
│   ├── middleware.py
│   └── api/
│       ├── jobs.py
│       ├── analytics.py
│       ├── recommend.py
│       ├── rag.py
│       └── health.py
│
├── pipeline/
│   ├── __init__.py
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
│
├── rag/
│   ├── chunking.py
│   ├── embeddings.py
│   ├── vector_store.py
│   ├── retriever.py
│   ├── filters.py
│   ├── qa.py
│   ├── answer_generation.py
│   └── llm_client.py
│
├── tests/
│   ├── test_ingest_utils.py
│   ├── test_recommendation_logic.py
│   ├── test_rag_logic.py
│   ├── test_answer_generation.py
│   ├── test_chunking.py
│   ├── test_skill_extraction.py
│   ├── test_jobs_query_params.py
│   └── test_filter_layer.py
│
├── data/
│   ├── raw/
│   │   └── jobs.csv
│   └── processed/
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
└── .env.example
```

---

## Pipeline

### 1. Ingestion

- reads `data/raw/jobs.csv`
- validates required fields
- normalizes selected fields
- upserts into PostgreSQL by URL

### 2. Processing

- cleans descriptions
- extracts skills using a rule-based taxonomy and alias mapping
- stores processed text for downstream use

### 3. Embeddings and Indexing

- builds job-level embeddings for recommendation
- builds chunk-level embeddings and FAISS index for retrieval
- stores generated artifacts in `data/processed/`

### 4. Recommendation

Hybrid recommendation combines:

- embedding similarity
- skill overlap
- category match
- seniority match

### 5. Retrieval / RAG

RAG flow includes:

- sentence-aware chunking
- semantic retrieval
- keyword reranking
- source deduplication
- optional LLM synthesis with extractive fallback

### 6. Operations

- `pipeline_runs` stores pipeline execution metadata
- `/health/indexes` returns artifact metadata
- `/health/pipeline` returns recent pipeline run summaries
- `pipeline/flows.py` defines the Prefect flow
- `pipeline/rebuild_all.py` runs the pipeline

---

## API

### GET /jobs

Supports:

- keyword, location, category, seniority  
- page, size  
- sort_by, sort_order  

```
GET /jobs?location=Berlin&category=Backend&seniority=Junior&page=1&size=10&sort_by=date_posted&sort_order=desc
```

---

### GET /analytics/skills

```
GET /analytics/skills?location=Berlin&category=Backend&seniority=Junior
```

---

### GET /recommend/{job_id}

- embedding score  
- skill overlap  
- metadata match  

```
GET /recommend/1?limit=5&same_category_only=true
```

---

### POST /rag/ask

```
{
  "question": "Which backend jobs require FastAPI and PostgreSQL?",
  "category": "Backend",
  "top_k": 3
}
```

---

### GET /health/indexes

- embedding / chunk index metadata  

---

## Running Locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

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