import argparse

from pipeline.flows import run_pipeline


def rebuild_all(full_rebuild: bool = False):
    if full_rebuild:
        print("Running pipeline in full rebuild mode.")
    else:
        print("Running pipeline in incremental mode.")

    run_pipeline(full_rebuild=full_rebuild)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--full-rebuild",
        action="store_true",
        help="Force all jobs to be marked dirty and reprocessed from ingest onward.",
    )
    args = parser.parse_args()

    rebuild_all(full_rebuild=args.full_rebuild)