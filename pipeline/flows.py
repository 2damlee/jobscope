from prefect import flow, task

from pipeline.build_chunk_index import build_chunk_index
from pipeline.build_embeddings import build_embeddings
from pipeline.ingest_jobs import ingest_jobs
from pipeline.process_jobs import process_jobs


@task(name="ingest_jobs", retries=2, retry_delay_seconds=5, log_prints=True)
def ingest_task(full_rebuild: bool = False):
    return ingest_jobs(full_rebuild=full_rebuild)


@task(name="process_jobs", retries=2, retry_delay_seconds=5, log_prints=True)
def process_task():
    return process_jobs()


@task(name="build_embeddings", retries=1, retry_delay_seconds=5, log_prints=True)
def embedding_task():
    return build_embeddings()


@task(name="build_chunk_index", retries=1, retry_delay_seconds=5, log_prints=True)
def chunk_task():
    return build_chunk_index()


@flow(name="jobscope_pipeline", log_prints=True)
def run_pipeline(full_rebuild: bool = False):
    ingest_summary = ingest_task(full_rebuild=full_rebuild)
    process_summary = process_task()
    embedding_summary = embedding_task()
    chunk_summary = chunk_task()

    return {
        "full_rebuild": full_rebuild,
        "ingest": ingest_summary,
        "process": process_summary,
        "embeddings": embedding_summary,
        "chunk_index": chunk_summary,
    }


if __name__ == "__main__":
    run_pipeline()