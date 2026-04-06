# JobScope

JobScope is a pipeline-oriented backend and data engineering project for ingesting, processing, indexing, and serving job posting data.

It demonstrates an end-to-end workflow across data ingestion, transformation, retrieval, recommendation, and API serving.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [API](#api)
- [Pipeline](#pipeline)
- [Evaluation](#evaluation)
- [Deployment](#deployment)
- [Running Locally](#running-locally)
- [What this project demonstrates](#what-this-project-demonstrates)

---

## Overview

Core flow:

CSV ingestion → PostgreSQL → cleaning / skill extraction → embeddings / chunk index → FastAPI APIs

This project focuses on:

* pipeline-oriented data processing
* API-based serving for search, analytics, recommendation, and retrieval

---

## Features

* CSV ingestion with validation, normalization, and URL-based upsert
* PostgreSQL-backed storage
* Cleaning and rule-based skill extraction
* Embedding-based similarity + hybrid recommendation
* Retrieval-based Q&A (chunking, semantic search, reranking, deduplication)
* Pipeline run tracking and health checks
* Prefect-based pipeline orchestration
* Docker-based deployment

---

## Tech Stack

* Python 3.11
* FastAPI
* PostgreSQL
* SQLAlchemy
* Prefect
* SentenceTransformers
* FAISS
* Docker

---

## Architecture

data/
raw/
processed/

app/
api/
services/
models/
crud/
schemas/

pipeline/
ingest_jobs.py
process_jobs.py
build_embeddings.py
build_chunk_index.py
flows.py

rag/
chunking.py
retriever.py
qa.py

---

## API

### GET /jobs

List jobs with filters, pagination, and sorting.

Query parameters:

* keyword: match against title or description
* location: filter by location
* category: filter by category
* seniority: filter by seniority
* page: page number (default: 1)
* size: page size (default: 20, max: 100)
* sort_by: date_posted, title, company, location, category, seniority
* sort_order: asc or desc

Response:

```json
{
  "items": [
    {
      "id": 1,
      "title": "Backend Engineer",
      "company": "Example",
      "location": "Berlin",
      "category": "Backend",
      "seniority": "Senior",
      "description": "...",
      "cleaned_description": "...",
      "detected_skills": "Python,FastAPI,PostgreSQL",
      "date_posted": "2024-03-01",
      "url": "https://example.com/job/1"
    }
  ],
  "page": 1,
  "size": 20,
  "total": 120
}
```

### GET /analytics/skills

Return top detected skills.

Query parameters:

* category
* seniority
* limit

---

### GET /recommend/{job_id}

Return similar jobs using hybrid scoring:

* embedding similarity
* skill overlap
* category match
* seniority match

---

### GET /health/indexes

Check whether embedding and chunk artifacts exist.

---

### GET /health/pipeline

Return pipeline run health summary.

---

### POST /rag/ask

Available only when ENABLE_RAG=true

Request:

```json
{
  "question": "Which backend jobs require FastAPI and PostgreSQL?",
  "category": "Backend",
  "location": "Berlin",
  "seniority": "Senior",
  "top_k": 3
}
```

---

## Pipeline

Run full pipeline:

```bash
python -m pipeline.rebuild_all --full-rebuild
```

Run incremental pipeline:

```bash
python -m pipeline.rebuild_all
```

Stages:

* ingest_jobs
* process_jobs
* build_embeddings
* build_chunk_index

---

## Evaluation

RAG evaluation:

```bash
python -m pipeline.evaluate_rag
```

Recommendation evaluation:

```bash
python -m pipeline.evaluate_recommendations
```

Outputs:

* data/processed/rag_eval_results.json
* data/processed/recommendation_eval_results.json

---

## Deployment

Live API:

https://jobscope-jrur.onrender.com/

* Root health check: GET /
* API docs: /docs
* Deployed with Docker and PostgreSQL

---

## Running Locally

1. Install dependencies

```bash
pip install -r requirements.txt
```

2. Set environment variables (.env)

```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/jobscope
```

3. Run pipeline

```bash
python -m pipeline.rebuild_all --full-rebuild
```

4. Start API

```bash
uvicorn app.main:app --reload
```

---

## What this project demonstrates

* End-to-end data pipeline design
* Backend API design with filtering, pagination, and validation
* Embedding-based retrieval and recommendation
* RAG-style question answering
* Pipeline orchestration and run tracking
* Docker-based deployment