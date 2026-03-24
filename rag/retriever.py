import json
import re

from rag.embeddings import embed_query
from rag.vector_store import load_faiss_index

CHUNK_META_PATH = "data/processed/job_chunks.json"


def tokenize(text: str) -> set[str]:
    if not text:
        return set()
    return set(re.findall(r"\b\w+\b", text.lower()))


def keyword_overlap_score(query: str, chunk_text: str) -> float:
    query_tokens = tokenize(query)
    chunk_tokens = tokenize(chunk_text)

    if not query_tokens or not chunk_tokens:
        return 0.0

    return len(query_tokens & chunk_tokens) / len(query_tokens)


def search_chunks(query: str, top_k: int = 5):
    index = load_faiss_index()

    with open(CHUNK_META_PATH, "r") as f:
        chunk_records = json.load(f)

    query_vector = embed_query(query)
    scores, indices = index.search(query_vector.reshape(1, -1), top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue

        meta = chunk_records[idx]
        keyword_score = keyword_overlap_score(query, meta["chunk_text"])

        results.append({
            "chunk_id": meta["chunk_id"],
            "job_id": meta["job_id"],
            "title": meta["title"],
            "company": meta["company"],
            "location": meta["location"],
            "category": meta["category"],
            "seniority": meta["seniority"],
            "chunk_text": meta["chunk_text"],
            "score": round(float(score), 4),
            "keyword_score": round(float(keyword_score), 4),
        })

    return results