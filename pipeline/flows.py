from prefect import flow, task

from pipeline.build_chunk_index import build_chunk_index
from pipeline.build_embeddings import build_embeddings
from pipeline.ingest_jobs import ingest_jobs
from pipeline.process_jobs import process_jobs


@task(name="ingest_jobs", retries=2, retry_delay_seconds=5, log_prints=True)
def ingest_task(full_rebuild: bool = False):
    print(f"[stage] ingest_jobs start (full_rebuild={full_rebuild})")
    result = ingest_jobs(full_rebuild=full_rebuild)
    print(f"[stage] ingest_jobs done: {result}")
    return result


@task(name="process_jobs", retries=2, retry_delay_seconds=5, log_prints=True)
def process_task():
    print("[stage] process_jobs start")
    result = process_jobs()
    print(f"[stage] process_jobs done: {result}")
    return result


@task(name="build_embeddings", retries=2, retry_delay_seconds=5, log_prints=True)
def embedding_task():
    print("[stage] build_embeddings start")
    result = build_embeddings()
    print(f"[stage] build_embeddings done: {result}")
    return result


@task(name="build_chunk_index", retries=2, retry_delay_seconds=5, log_prints=True)
def chunk_task():
    print("[stage] build_chunk_index start")
    result = build_chunk_index()
    print(f"[stage] build_chunk_index done: {result}")
    return result


@flow(name="jobscope_pipeline", log_prints=True)
def run_pipeline(full_rebuild: bool = False):
    ingest_summary = ingest_task(full_rebuild=full_rebuild)
    process_summary = process_task()
    embedding_summary = embedding_task()
    chunk_summary = chunk_task()

    pipeline_summary = {
        "full_rebuild": full_rebuild,
        "ingest": ingest_summary,
        "process": process_summary,
        "embeddings": embedding_summary,
        "chunk_index": chunk_summary,
    }

    print(f"[pipeline] summary: {pipeline_summary}")
    return pipeline_summary