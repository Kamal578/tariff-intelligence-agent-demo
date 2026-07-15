from __future__ import annotations

from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse

from app.config import get_settings
from app.connectors.router import get_source_document, load_source_documents, search_all_sources, source_stats
from app.jobs import create_analysis_job, get_analysis_job, list_analysis_jobs, run_analysis_job, summarize_processing_result
from app.pipeline import (
    ingest_knowledge,
    load_issues_state,
    load_proposals_state,
    load_records_state,
    process_tariffs,
)
from app.reporting import apply_approved_updates, build_run_package, generate_markdown_report, load_audit_log
from app.review_store import load_review_decisions, save_review_decision
from app.schemas import ProcessRequest, ReviewDecision


app = FastAPI(title="Tariff Intelligence Agent Demo", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/config/status")
def config_status() -> dict[str, object]:
    settings = get_settings()
    stats = source_stats(settings)
    source_counts = stats["source_counts"]
    return {
        "environment": settings.app_env,
        "gemini_configured": bool(settings.gemini_api_key),
        "gemini_model": settings.gemini_model,
        "input_excel": str(settings.input_excel_path),
        "output_dir": str(settings.output_dir),
        "mock_sources_ready": sum(source_counts.values()) > 0,
        "source_counts": source_counts,
        "real_connectors_used": stats["real_connectors_used"],
    }


@app.post("/ingest")
def ingest() -> dict[str, object]:
    return ingest_knowledge(get_settings())


@app.post("/process")
def process(request: ProcessRequest | None = None) -> dict[str, object]:
    request = request or ProcessRequest()
    result = process_tariffs(get_settings(), generation_mode=request.mode)
    return summarize_processing_result(result).model_dump(mode="json")


@app.post("/analysis-jobs")
def start_analysis_job(request: ProcessRequest, background_tasks: BackgroundTasks) -> dict[str, object]:
    settings = get_settings()
    job = create_analysis_job(request.mode, settings)
    background_tasks.add_task(run_analysis_job, job.job_id, settings)
    return job.model_dump(mode="json")


@app.get("/analysis-jobs")
def analysis_jobs() -> list[dict[str, object]]:
    return [job.model_dump(mode="json") for job in list_analysis_jobs(get_settings())]


@app.get("/analysis-jobs/{job_id}")
def analysis_job(job_id: str) -> dict[str, object]:
    job = get_analysis_job(job_id, get_settings())
    if job is None:
        raise HTTPException(status_code=404, detail=f"Analysis job {job_id} not found")
    return job.model_dump(mode="json")


@app.get("/records")
def records() -> list[dict[str, object]]:
    return [record.model_dump(mode="json") for record in load_records_state(get_settings())]


@app.get("/proposals")
def proposals() -> list[dict[str, object]]:
    return [proposal.model_dump(mode="json") for proposal in load_proposals_state(get_settings())]


@app.get("/proposals/{proposal_id}")
def proposal_detail(proposal_id: str) -> dict[str, object]:
    for proposal in load_proposals_state(get_settings()):
        if proposal.proposal_id == proposal_id:
            return proposal.model_dump(mode="json")
    raise HTTPException(status_code=404, detail=f"Proposal {proposal_id} not found")


@app.post("/review")
def review(decision: ReviewDecision) -> dict[str, object]:
    proposals_after_review = save_review_decision(decision, get_settings())
    return {
        "saved": True,
        "decision": decision.model_dump(mode="json"),
        "proposal_count": len(proposals_after_review),
        "decisions": [item.model_dump(mode="json") for item in load_review_decisions(get_settings())],
    }


@app.post("/apply-approved")
def apply_approved() -> dict[str, object]:
    try:
        return apply_approved_updates(get_settings())
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/audit-log")
def audit_log() -> list[dict[str, object]]:
    return load_audit_log(get_settings())


@app.get("/report", response_model=None)
def report() -> FileResponse | PlainTextResponse:
    settings = get_settings()
    if not settings.report_path.exists():
        generate_markdown_report(settings=settings)
    if settings.report_path.exists():
        return FileResponse(settings.report_path, media_type="text/markdown")
    return PlainTextResponse("Report has not been generated yet.", status_code=404)


@app.get("/download/updated-excel", response_model=None)
def download_updated_excel() -> FileResponse:
    settings = get_settings()
    return _download(settings.updated_excel_path, "updated_tariff_packs.xlsx")


@app.get("/download/audit-json", response_model=None)
def download_audit_json() -> FileResponse:
    settings = get_settings()
    return _download(settings.audit_log_path, "audit_log.json")


@app.get("/download/report-md", response_model=None)
def download_report_md() -> FileResponse:
    settings = get_settings()
    if not settings.report_path.exists():
        generate_markdown_report(settings=settings)
    return _download(settings.report_path, "report.md")


@app.get("/download/run-package", response_model=None)
def download_run_package() -> FileResponse:
    settings = get_settings()
    build_run_package(settings)
    return _download(settings.run_package_path, "analysis_run_package.zip")


@app.get("/sources/search")
def source_search(q: str = Query(..., min_length=2)) -> list[dict[str, object]]:
    return [item.model_dump(mode="json") for item in search_all_sources(q, settings=get_settings())]


@app.get("/sources")
def sources() -> list[dict[str, object]]:
    return load_source_documents(get_settings())


@app.get("/sources/stats")
def sources_stats() -> dict[str, object]:
    return source_stats(get_settings())


@app.get("/sources/{source_id}")
def source_detail(source_id: str) -> dict[str, object]:
    document = get_source_document(source_id, get_settings())
    if document is None:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
    return document


@app.post("/reset-demo")
def reset_demo() -> dict[str, object]:
    settings = get_settings()
    removed: list[str] = []
    for path in [
        settings.records_state_path,
        settings.issues_state_path,
        settings.proposals_state_path,
        settings.review_state_path,
        settings.audit_log_path,
        settings.report_path,
        settings.updated_excel_path,
        settings.analysis_runs_path,
        settings.run_package_path,
    ]:
        if path.exists():
            path.unlink()
            removed.append(str(path))
    return {"reset": True, "removed": removed}


@app.get("/metrics")
def metrics() -> dict[str, object]:
    proposals_state = load_proposals_state(get_settings())
    decisions = load_review_decisions(get_settings())
    return {
        "records": len(load_records_state(get_settings())),
        "issues": len(load_issues_state(get_settings())),
        "proposals": len(proposals_state),
        "high_risk_proposals": sum(1 for item in proposals_state if item.risk_level == "high"),
        "approved_updates": sum(1 for item in decisions if item.decision == "approved"),
        "rejected_updates": sum(1 for item in decisions if item.decision == "rejected"),
        "source_conflicts": sum(1 for item in proposals_state if item.source_conflict_detected),
    }


def _download(path: Path, filename: str) -> FileResponse:
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"{filename} has not been generated yet")
    return FileResponse(path, filename=filename)
