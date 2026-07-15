from __future__ import annotations

from datetime import UTC, datetime
from threading import Lock
from uuid import uuid4

from app.config import Settings, get_settings
from app.pipeline import process_tariffs, read_json, write_json
from app.schemas import AnalysisJob, AnalysisMode, ProcessSummary, ProcessingResult


_LOCK = Lock()


def create_analysis_job(mode: AnalysisMode, settings: Settings | None = None) -> AnalysisJob:
    settings = settings or get_settings()
    job = AnalysisJob(
        job_id=f"run-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}",
        requested_mode=mode,
    )
    _upsert_job(job, settings)
    return job


def run_analysis_job(job_id: str, settings: Settings | None = None) -> AnalysisJob:
    settings = settings or get_settings()
    job = get_analysis_job(job_id, settings)
    if job is None:
        raise ValueError(f"Analysis job {job_id} not found")

    job.status = "running"
    job.stage = "Starting analysis"
    job.progress = 5
    job.started_at = datetime.now(UTC)
    _upsert_job(job, settings)

    try:
        result = process_tariffs(
            settings,
            generation_mode=job.requested_mode,
            progress_callback=lambda stage, progress: _update_progress(job_id, stage, progress, settings),
        )
        job = get_analysis_job(job_id, settings) or job
        job.status = "completed"
        job.stage = "Completed"
        job.progress = 100
        job.actual_mode = result.mode
        job.summary = summarize_processing_result(result)
        job.finished_at = datetime.now(UTC)
        _upsert_job(job, settings)
        return job
    except Exception as exc:
        job = get_analysis_job(job_id, settings) or job
        job.status = "failed"
        job.stage = "Failed"
        job.error = str(exc)
        job.finished_at = datetime.now(UTC)
        _upsert_job(job, settings)
        return job


def list_analysis_jobs(settings: Settings | None = None) -> list[AnalysisJob]:
    settings = settings or get_settings()
    jobs = [AnalysisJob.model_validate(item) for item in read_json(settings.analysis_runs_path, [])]
    return sorted(jobs, key=lambda item: item.created_at, reverse=True)


def get_analysis_job(job_id: str, settings: Settings | None = None) -> AnalysisJob | None:
    for job in list_analysis_jobs(settings):
        if job.job_id == job_id:
            return job
    return None


def summarize_processing_result(result: ProcessingResult) -> ProcessSummary:
    return ProcessSummary(
        records=len(result.records),
        issues=len(result.issues),
        proposals=len(result.proposals),
        high_risk_proposals=sum(1 for item in result.proposals if item.risk_level == "high"),
        source_conflicts=sum(1 for item in result.proposals if item.source_conflict_detected),
        mode=result.mode,
        generated_at=result.generated_at,
    )


def _update_progress(job_id: str, stage: str, progress: int, settings: Settings) -> None:
    job = get_analysis_job(job_id, settings)
    if job is None:
        return
    job.stage = stage
    job.progress = progress
    _upsert_job(job, settings)


def _upsert_job(job: AnalysisJob, settings: Settings) -> None:
    with _LOCK:
        existing = [
            AnalysisJob.model_validate(item)
            for item in read_json(settings.analysis_runs_path, [])
        ]
        by_id = {item.job_id: item for item in existing}
        job.updated_at = datetime.now(UTC)
        by_id[job.job_id] = job
        jobs = sorted(by_id.values(), key=lambda item: item.created_at, reverse=True)
        write_json(settings.analysis_runs_path, [item.model_dump(mode="json") for item in jobs])
