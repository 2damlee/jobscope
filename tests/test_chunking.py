from rag.chunking import split_into_sentences, merge_short_sentences, chunk_text


def test_split_into_sentences():
    text = "Build APIs with FastAPI. Use PostgreSQL for storage. Deploy with Docker."
    sentences = split_into_sentences(text)
    assert len(sentences) == 3


def test_merge_short_sentences():
    sentences = ["SQL reports.", "Build dashboards for business teams.", "Python automation is required."]
    merged = merge_short_sentences(sentences, min_sentence_length=20)
    assert len(merged) <= len(sentences)


def test_chunk_text_returns_non_empty_chunks():
    text = (
        "Build backend APIs using Python and FastAPI. "
        "Use PostgreSQL for data storage and query optimization. "
        "Deploy services with Docker in cloud environments. "
        "Collaborate with product teams and improve service reliability."
    )

    chunks = chunk_text(text, target_chunk_size=120, max_chunk_size=180, overlap_sentences=1)

    assert len(chunks) >= 1
    assert all(len(chunk) >= 40 for chunk in chunks)