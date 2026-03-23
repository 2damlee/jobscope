# JobScope: AI-Powered Job Intelligence Platform

JobScope is a backend/data project that processes job postings and provides skill analysis, similar job recommendations, and retrieval-based question answering.

The project was built as a portfolio-focused MVP with an end-to-end flow:

CSV ingestion → PostgreSQL storage → text cleaning → skill extraction → embeddings/retrieval → FastAPI APIs.

---

## What it does

- Ingests job posting data from CSV into PostgreSQL
- Cleans job descriptions for downstream analytics and retrieval
- Extracts core skills with a rule-based approach
- Exposes a job listing API with simple filters
- Provides top skill analytics
- Recommends similar jobs using description embeddings
- Supports RAG-style Q&A over job description chunks with source metadata

---

## Why I built it

I wanted a project that combines data engineering, backend development, and applied NLP in one system.

Instead of building a frontend-heavy app, I focused on:

- data flow
- API design
- database modeling
- semantic similarity
- retrieval-based question answering
- reproducible local execution with Docker

---

## Scope

### Included in MVP

- CSV-based job ingestion
- PostgreSQL storage
- description cleaning
- rule-based skill extraction
- /jobs
- /analytics/skills
- /recommend/{job_id}
- /rag/ask
- Docker setup

### Not included

- frontend
- production-grade web crawling
- Airflow / Kafka / Kubernetes
- resume-job matching
- CI/CD

---

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Pandas
- sentence-transformers
- FAISS
- Docker

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
│   └── api/
│       ├── jobs.py
│       ├── analytics.py
│       ├── recommend.py
│       └── rag.py
│
├── pipeline/
│   ├── create_tables.py
│   ├── ingest_jobs.py
│   ├── clean_jobs.py
│   ├── extract_skills.py
│   ├── process_jobs.py
│   ├── build_embeddings.py
│   ├── build_chunk_index.py
│   └── test_chunk_search.py
│
├── rag/
│   ├── chunking.py
│   ├── embeddings.py
│   ├── vector_store.py
│   ├── retriever.py
│   └── qa.py
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

## Architecture

```
CSV
 → ingestion
 → PostgreSQL
 → cleaning / skill extraction
 → job embeddings / chunk embeddings
 → FAISS index
 → FastAPI APIs
```

---

## Data Model

### jobs

Main job posting table.

Fields:

- id
- title
- company
- location
- category
- seniority
- description
- cleaned_description
- detected_skills
- date_posted
- url

---

## Pipeline Overview

### 1. Ingestion

Job postings are loaded from CSV and inserted into PostgreSQL.

### 2. Cleaning

Descriptions are normalized into cleaned_description for analytics and semantic retrieval.

### 3. Skill Extraction

A compact rule-based dictionary is used to detect common skills such as:

- Python
- SQL
- FastAPI
- Docker
- AWS
- PyTorch
- ETL

The extracted result is stored in detected_skills.

### 4. Recommendation

Job descriptions are embedded with all-MiniLM-L6-v2.

Similarity is computed over normalized embeddings to return related job postings.

### 5. Retrieval / RAG

Job descriptions are chunked, embedded, and indexed with FAISS.

The /rag/ask endpoint retrieves relevant chunks and returns:

- answer
- matched chunks
- source metadata

---

## API Endpoints

### GET /jobs

Returns stored job postings.

Supports:

- keyword
- location
- category
- limit

Example:

```
GET /jobs?location=Berlin&category=Backend&limit=10
```

---

### GET /analytics/skills

Returns top detected skills.

Supports:

- category
- seniority
- limit

Example:

```
GET /analytics/skills?category=Analytics&seniority=Junior
```

---

### GET /recommend/{job_id}

Returns similar jobs based on description embeddings.

Example:

```
GET /recommend/1?limit=5
```

---

### POST /rag/ask

Retrieval-based Q&A over job description chunks.

Example request:

```json
{
  "question": "Which backend jobs require FastAPI and PostgreSQL?",
  "category": "Backend",
  "top_k": 3
}
```

Example response:

```json
{
  "answer": "...",
  "sources": [
    {
      "job_id": 1,
      "title": "Backend Engineer",
      "company": "HelloTech GmbH",
      "location": "Berlin",
      "category": "Backend",
      "seniority": "Junior",
      "chunk_id": 0,
      "score": 0.82
    }
  ],
  "matched_chunks": [
    "build and maintain backend apis using python fastapi postgresql and docker ..."
  ]
}
```

---

## Sample Data

The current MVP uses manually curated Germany-based sample postings to validate:

- ingestion flow
- analytics logic
- recommendation behavior
- retrieval quality

### Cities included

- Berlin
- Munich
- Frankfurt
- Hamburg
- Cologne
- Stuttgart
- Dusseldorf
- Leipzig

### Categories included

- Backend
- Data
- Analytics
- ML

---

## Running Locally

### 1. Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set environment variables

Create .env from .env.example.

Example:

```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/jobscope
```

### 4. Run API

```bash
uvicorn app.main:app --reload
```

Docs:

```
http://127.0.0.1:8000/docs
```

---

## Running with Docker

### 1. Start services

```bash
docker compose up --build
```

### 2. Initialize data

```bash
docker compose exec api python -m pipeline.create_tables
docker compose exec api python -m pipeline.ingest_jobs
docker compose exec api python -m pipeline.process_jobs
docker compose exec api python -m pipeline.build_embeddings
docker compose exec api python -m pipeline.build_chunk_index
```

### 3. Open docs

```
http://127.0.0.1:8000/docs
```

---

## Example Workflow

A typical setup flow:

1. Start PostgreSQL and API
2. Create database tables
3. Load CSV job postings
4. Clean descriptions and extract skills
5. Build job embeddings for recommendation
6. Build chunk index for retrieval
7. Query APIs via Swagger or curl
