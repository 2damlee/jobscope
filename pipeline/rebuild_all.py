from prefect import flow, task

from pipeline.build_chunk_index import build_chunk_index
from pipeline.build_embeddings import build_embeddings
from pipeline.ingest_jobs import ingest_jobs
from pipeline.process_jobs import process_jobs


@task(name="ingest_jobs", retries=2, retry_delay_seconds=5, log_prints=True)
def ingest_task(full_rebuild: bool = False):
    ingest_jobs(full_rebuild=full_rebuild)


@task(name="process_jobs", retries=2, retry_delay_seconds=5, log_prints=True)
def process_task():
    process_jobs()


@task(name="build_embeddings", retries=1, retry_delay_seconds=5, log_prints=True)
def embeddings_task(full_rebuild: bool = False):
    build_embeddings(full_rebuild=full_rebuild)


@task(name="build_chunk_index", retries=1, retry_delay_seconds=5, log_prints=True)
def chunk_index_task(full_rebuild: bool = False):
    build_chunk_index(full_rebuild=full_rebuild)


@flow(name="jobscope_pipeline", log_prints=True)
def run_pipeline(full_rebuild: bool = False):
    ingest_task(full_rebuild=full_rebuild)
    process_task()
    embeddings_task(full_rebuild=full_rebuild)
    chunk_index_task(full_rebuild=full_rebuild)


if __name__ == "__main__":
    run_pipeline()