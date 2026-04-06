import argparse
import json

from pipeline.flows import run_pipeline


def rebuild_all(full_rebuild: bool = False):
    print(
        "Running pipeline in full rebuild mode."
        if full_rebuild
        else "Running pipeline in incremental mode."
    )

    summary = run_pipeline(full_rebuild=full_rebuild)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--full-rebuild",
        action="store_true",
        help="Force all jobs to be marked dirty and reprocessed from ingest onward.",
    )
    args = parser.parse_args()
    rebuild_all(full_rebuild=args.full_rebuild)