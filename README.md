# JobScope: AI-Powered Job Intelligence Platform

JobScope is a pipeline-oriented backend/data system for ingesting, processing, and serving job posting data.

It focuses on combining data engineering workflows with API-based serving, recommendation, and retrieval.

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

- CSV ingestion with validation and upsert logic  
- PostgreSQL-backed storage  
- Job description cleaning  
- Rule-based skill extraction (alias normalization)  
- Job API with filtering, sorting, pagination  
- Skill analytics  
- Hybrid recommendation (embeddings + structured signals)  
- Retrieval-based Q&A (RAG pipeline)  

---

## Tech Stack

- Python, FastAPI  
- PostgreSQL, SQLAlchemy  
- Pandas  
- sentence-transformers  
- FAISS  
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
│   ├── create_tables.py
│   ├── ingest_jobs.py
│   ├── clean_jobs.py
│   ├── extract_skills.py
│   ├── process_jobs.py
│   ├── build_embeddings.py
│   ├── build_chunk_index.py
│   ├── evaluate_rag.py
│   ├── rebuild_all.py
│   └── skill_dict.py
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

- CSV → PostgreSQL
- required field validation  
- URL-based upsert  
- normalization (location / category / seniority)  
- inserted / updated / skipped tracking  

---

### 2. Cleaning

- description → cleaned_description  
- used for analytics, recommendation, retrieval  

---

### 3. Skill Extraction

- rule-based taxonomy + alias handling  

Examples:

- postgres, postgresql → postgresql  
- sklearn, scikit learn → scikit-learn  

- stored in detected_skills  

---

### 4. Recommendation

- embeddings: all-MiniLM-L6-v2  

Hybrid scoring:

- embedding similarity  
- skill overlap  
- category match  
- seniority match  

---

### 5. Retrieval / RAG

- sentence-aware chunking  
- FAISS indexing  

Includes:

- semantic retrieval  
- keyword-based reranking  
- source deduplication  
- optional LLM synthesis (fallback: extractive)  

---

### 6. Rebuild & Evaluation

- pipeline/rebuild_all.py  
- pipeline/evaluate_rag.py  

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