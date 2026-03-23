import json

from rag.embeddings import embed_query
from rag.vector_store import load_faiss_index

CHUNK_META_PATH = "data/processed/job_chunks.json"


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
        })

    return results