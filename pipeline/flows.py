from prefect import flow, task

from pipeline.build_chunk_index import build_chunk_index
from pipeline.build_embeddings import build_embeddings
from pipeline.ingest_jobs import ingest_jobs
from pipeline.process_jobs import process_jobs


@task(name="ingest_jobs", retries=2, retry_delay_seconds=5, log_prints=True)
def ingest_task():
    ingest_jobs()


@task(name="process_jobs", retries=2, retry_delay_seconds=5, log_prints=True)
def process_task():
    process_jobs()


@task(name="build_embeddings", retries=1, retry_delay_seconds=5, log_prints=True)
def embeddings_task():
    build_embeddings()


@task(name="build_chunk_index", retries=1, retry_delay_seconds=5, log_prints=True)
def chunk_index_task():
    build_chunk_index()


@flow(name="jobscope_pipeline", log_prints=True)
def run_pipeline():
    ingest_task()
    process_task()
    embeddings_task()
    chunk_index_task()


if __name__ == "__main__":
    run_pipeline()