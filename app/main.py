from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse

from app.config import get_settings
from app.pipeline import ingest_knowledge, load_proposals_state, load_records_state, process_tariffs
from app.reporting import apply_approved_updates, generate_markdown_report
from app.review_store import load_review_decisions, save_review_decision
from app.schemas import ReviewDecision


app = FastAPI(title="Tariff Intelligence Agent Demo", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ingest")
def ingest() -> dict[str, object]:
    return ingest_knowledge(get_settings())


@app.post("/process")
def process() -> dict[str, object]:
    result = process_tariffs(get_settings())
    return {
        "records": len(result.records),
        "issues": len(result.issues),
        "proposals": len(result.proposals),
        "mode": result.mode,
        "generated_at": result.generated_at,
    }


@app.get("/records")
def records() -> list[dict[str, object]]:
    return [record.model_dump(mode="json") for record in load_records_state(get_settings())]


@app.get("/proposals")
def proposals() -> list[dict[str, object]]:
    return [proposal.model_dump(mode="json") for proposal in load_proposals_state(get_settings())]


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


@app.get("/report", response_model=None)
def report() -> FileResponse | PlainTextResponse:
    settings = get_settings()
    if not settings.report_path.exists():
        generate_markdown_report(settings=settings)
    if settings.report_path.exists():
        return FileResponse(settings.report_path, media_type="text/markdown")
    return PlainTextResponse("Report has not been generated yet.", status_code=404)
