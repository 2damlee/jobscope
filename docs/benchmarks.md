# JobScope Performance Benchmarks

All measurements are reproducible via `scripts/benchmark.py`.

**Environment**
- MacBook Air (Apple Silicon), <8/16> GB RAM
- PostgreSQL 16 (Docker), Python 3.11
- App: uvicorn, single worker
- Benchmark: 200 requests per endpoint, concurrency 8, 5 warmup requests

**Dataset**
- Source: Kaggle LinkedIn Job Postings (123,849 raw postings)
- After tech-role filtering & cleaning (`scripts/prepare_kaggle_jobs.py`): 18,523 rows
- Jobs in DB after ingest: 18,988

## Pipeline throughput (full rebuild)

| Stage | Output | Wall time |
|---|---|---|
| Ingest (CSV → PostgreSQL upsert) | 18,523 rows (17,653 inserted / 870 updated) | 39 s |
| Process (cleaning + skill extraction) | 18,988 jobs, avg 2.69 skills/job | 1 min 13 s |
| Embedding build (all-MiniLM-L6-v2, batch 64) | 18,988 vectors | 2 min 15 s |
| RAG chunk index (FAISS) | 227,539 chunks | 13 min 18 s |

The chunk index is by far the most expensive stage (~4× longer than all
other stages combined) — a candidate for incremental rebuilds.

## API latency

### Baseline — before optimization

Label: `before: full dataset, naive recommend + ILIKE search`
(raw data: `docs/benchmark_before.json`)

| Endpoint | p50 (ms) | p95 (ms) | p99 (ms) | mean (ms) | errors |
|---|---|---|---|---|---|
| `GET /jobs?keyword=` | 3,084 | 3,532 | 3,708 | 3,111 | 0 |
| `GET /jobs/{id}/recommendations` | 11,501 | 18,186 | 21,453 | 11,448 | 0 |

**Diagnosis**
- `/jobs?keyword=`: `ILIKE '%kw%'` over three text columns cannot use an
  index → sequential scan over ~19k rows per request.
- `/recommendations`: per request, the service computes similarity against
  the **entire** embedding matrix and loads **all** candidate jobs from the
  database before ranking — O(N) DB fetch + O(N) scoring on every

### After optimization

**Two-stage retrieval** (`after: FAISS two-stage candidate retrieval`,
raw data: `docs/benchmark_after_day4.json`)

| Endpoint | Stage | p50 (ms) | p95 (ms) | p99 (ms) |
|---|---|---|---|---|
| `GET /jobs/{id}/recommendations` | before (full scan) | 11,501 | 18,186 | 21,453 |
| `GET /jobs/{id}/recommendations` | **after (FAISS 2-stage)** | **67** | **119** | **155** |
| `GET /jobs?keyword=` | before (ILIKE) | 3,084 | 3,532 | 3,708 |
| `GET /jobs?keyword=` | after (FTS + GIN) | – (Day 5) | – | – |

**~172× p50 improvement.** Candidate generation is exact (IndexFlatIP), so
the top-K set is mathematically identical to the previous full scan; offline
evaluation confirmed no quality regression (14/14 sampled jobs produce
recommendations, all with shared skills, avg 5.0 per job).