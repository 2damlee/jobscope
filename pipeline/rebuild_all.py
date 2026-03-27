import argparse

from pipeline.ingest_jobs import ingest_jobs
from pipeline.process_jobs import process_jobs
from pipeline.build_embeddings import build_embeddings
from pipeline.build_chunk_index import build_chunk_index


def rebuild_all(full_rebuild: bool = False):
    if full_rebuild:
        print("Running full rebuild mode.")
    else:
        print("Running incremental rebuild mode.")

    print("[1/4] ingest_jobs")
    ingest_jobs()

    print("[2/4] process_jobs")
    process_jobs()

    print("[3/4] build_embeddings")
    build_embeddings()

    print("[4/4] build_chunk_index")
    build_chunk_index()

    print("Rebuild completed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--full-rebuild",
        action="store_true",
        help="Force full pipeline rebuild.",
    )
    args = parser.parse_args()

    rebuild_all(full_rebuild=args.full_rebuild)