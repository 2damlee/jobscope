# JobScope: AI-Powered Job Intelligence Platform

JobScope is a backend/data project that processes job postings and provides skill analysis, similar job recommendations, and retrieval-based question answering.

The project was built as a portfolio-focused MVP with an end-to-end flow:

CSV ingestion → PostgreSQL storage → text cleaning → skill extraction → embeddings/retrieval → FastAPI APIs.

---

## What it does

- Ingests job posting data from CSV into PostgreSQL
- Cleans job descriptions for downstream analytics and retrieval
- Extracts normalized core skills with a rule-based taxonomy and alias handling
- Exposes a job listing API with simple filters
- Provides top skill analytics
- Recommends similar jobs using hybrid scoring over embeddings and structured signals
- Supports retrieval-based Q&A with reranking, source deduplication, sentence-aware chunking, and optional LLM synthesis

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
│   ├── qa.py
│   └── answer_generation.py
│
├── tests/
│   ├── test_ingest_utils.py
│   ├── test_recommendation_logic.py
│   ├── test_rag_logic.py
│   ├── test_answer_generation.py
│   └── test_chunking.py
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