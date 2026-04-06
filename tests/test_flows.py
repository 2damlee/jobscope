from pipeline import flows


def test_run_pipeline_returns_stage_summaries(monkeypatch):
    monkeypatch.setattr(
        flows,
        "ingest_task",
        lambda full_rebuild=False: {
            "changed_rows": 3,
            "full_rebuild": full_rebuild,
        },
    )
    monkeypatch.setattr(
        flows,
        "process_task",
        lambda: {"processed_jobs": 3},
    )
    monkeypatch.setattr(
        flows,
        "embedding_task",
        lambda: {"skipped_rebuild": False, "embedded_jobs": 3},
    )
    monkeypatch.setattr(
        flows,
        "chunk_task",
        lambda: {"skipped_rebuild": True, "dirty_jobs": 0},
    )

    result = flows.run_pipeline(full_rebuild=False)

    assert result["full_rebuild"] is False
    assert result["ingest"]["changed_rows"] == 3
    assert result["process"]["processed_jobs"] == 3
    assert result["embeddings"]["embedded_jobs"] == 3
    assert result["chunk_index"]["skipped_rebuild"] is True