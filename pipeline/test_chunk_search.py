from rag.retriever import search_chunks


if __name__ == "__main__":
    query = "Which backend jobs require FastAPI and PostgreSQL?"
    results = search_chunks(query, top_k=5)

    for r in results:
        print("=" * 80)
        print(f"job_id: {r['job_id']}")
        print(f"title: {r['title']}")
        print(f"score: {r['score']}")
        print(f"chunk: {r['chunk_text']}")