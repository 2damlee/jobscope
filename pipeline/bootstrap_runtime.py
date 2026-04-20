import argparse
import subprocess
import sys


def run_step(command: list[str]) -> None:
    print(f"\n[RUN] {' '.join(command)}")
    result = subprocess.run(command)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap JobScope runtime state.")
    parser.add_argument(
        "--full-rebuild",
        action="store_true",
        help="Run pipeline in full rebuild mode.",
    )
    args = parser.parse_args()

    python = sys.executable

    run_step([python, "-m", "pipeline.wait_for_db"])
    run_step(["alembic", "upgrade", "head"])

    rebuild_command = [python, "-m", "pipeline.rebuild_all"]
    if args.full_rebuild:
        rebuild_command.append("--full-rebuild")

    run_step(rebuild_command)

    print("\nBootstrap completed successfully.")


if __name__ == "__main__":
    main()