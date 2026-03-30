from prefect import flow, task

from pipeline.build_chunk_index import build_chunk_index
from pipeline.build_embeddings import build_embeddings
from pipeline.ingest_jobs import ingest_jobs
from pipeline.process_jobs import process_jobs


@task(name="ingest_jobs", retries=2, retry_delay_seconds=5, log_prints=True)
def ingest_task(full_rebuild: bool = False):
    print(f"[stage] ingest_jobs start (full_rebuild={full_rebuild})")
    ingest_jobs(full_rebuild=full_rebuild)
    print("[stage] ingest_jobs done")


@task(name="process_jobs", retries=2, retry_delay_seconds=5, log_prints=True)
def process_task():
    print("[stage] process_jobs start")
    process_jobs()
    print("[stage] process_jobs done")


@task(name="build_embeddings", retries=1, retry_delay_seconds=5, log_prints=True)
def embeddings_task():
    print("[stage] build_embeddings start")
    build_embeddings()
    print("[stage] build_embeddings done")


@task(name="build_chunk_index", retries=1, retry_delay_seconds=5, log_prints=True)
def chunk_index_task():
    print("[stage] build_chunk_index start")
    build_chunk_index()
    print("[stage] build_chunk_index done")


@flow(name="jobscope_pipeline", log_prints=True)
def run_pipeline(full_rebuild: bool = False):
    print(f"[flow] jobscope_pipeline start (full_rebuild={full_rebuild})")

    ingest_task(full_rebuild=full_rebuild)
    process_task()
    embeddings_task()
    chunk_index_task()

    print("[flow] jobscope_pipeline completed")


if __name__ == "__main__":
    run_pipeline()