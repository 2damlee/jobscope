from datetime import datetime

from app.models import PipelineRun


def start_run(
    db,
    pipeline_name: str,
    source_name: str | None = None,
    input_rows: int | None = None,
):
    run = PipelineRun(
        pipeline_name=pipeline_name,
        status="started",
        source_name=source_name,
        input_rows=input_rows,
        started_at=datetime.utcnow(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def finish_run(
    db,
    run: PipelineRun,
    *,
    status: str,
    output_rows: int | None = None,
    inserted_rows: int | None = None,
    updated_rows: int | None = None,
    skipped_rows: int | None = None,
    metrics: dict | None = None,
    error_message: str | None = None,
):
    finished_at = datetime.utcnow()
    duration_seconds = None

    if run.started_at:
        duration_seconds = round((finished_at - run.started_at).total_seconds(), 3)

    merged_metrics = dict(metrics or {})
    merged_metrics["duration_seconds"] = duration_seconds

    run.status = status
    run.output_rows = output_rows
    run.inserted_rows = inserted_rows
    run.updated_rows = updated_rows
    run.skipped_rows = skipped_rows
    run.metrics = merged_metrics
    run.error_message = error_message
    run.finished_at = finished_at

    db.commit()
    db.refresh(run)
    return run