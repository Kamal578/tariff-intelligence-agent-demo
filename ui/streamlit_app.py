from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx
import pandas as pd
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
OUTPUT_DIR = Path("data/output")


def api_request(method: str, path: str, **kwargs: Any) -> Any:
    url = f"{API_BASE_URL.rstrip('/')}{path}"
    with httpx.Client(timeout=60.0) as client:
        response = client.request(method, url, **kwargs)
        response.raise_for_status()
        if response.headers.get("content-type", "").startswith("application/json"):
            return response.json()
        return response.text


def load_api_table(path: str) -> pd.DataFrame:
    try:
        payload = api_request("GET", path)
    except Exception:
        return pd.DataFrame()
    return pd.DataFrame(payload)


def render_download(label: str, path: Path, mime: str) -> None:
    if path.exists():
        st.download_button(label, data=path.read_bytes(), file_name=path.name, mime=mime)
    else:
        st.button(label, disabled=True)


st.set_page_config(page_title="Tariff Intelligence Agent Demo", layout="wide")
st.title("Tariff Intelligence Agent Demo")
st.caption(
    "Synthetic Excel remediation workflow: detect tariff data issues, retrieve evidence, "
    "generate structured proposals, review changes, and export approved updates."
)

with st.sidebar:
    st.subheader("Backend")
    st.code(API_BASE_URL)
    try:
        health = api_request("GET", "/health")
        st.success(f"API status: {health['status']}")
    except Exception as exc:
        st.error(f"API unavailable: {exc}")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Build Knowledge Index", use_container_width=True):
        try:
            st.session_state["ingest_result"] = api_request("POST", "/ingest")
        except Exception as exc:
            st.session_state["ingest_error"] = str(exc)
with col2:
    if st.button("Run Tariff Analysis", use_container_width=True):
        try:
            st.session_state["process_result"] = api_request("POST", "/process")
        except Exception as exc:
            st.session_state["process_error"] = str(exc)
with col3:
    if st.button("Apply Approved Updates", use_container_width=True):
        try:
            st.session_state["apply_result"] = api_request("POST", "/apply-approved")
        except Exception as exc:
            st.session_state["apply_error"] = str(exc)

for key, label in [
    ("ingest_result", "Knowledge index"),
    ("process_result", "Analysis"),
    ("apply_result", "Apply approved"),
]:
    if key in st.session_state:
        st.info(f"{label}: {st.session_state[key]}")

for key in ["ingest_error", "process_error", "apply_error"]:
    if key in st.session_state:
        st.warning(st.session_state[key])

records_df = load_api_table("/records")
proposals_df = load_api_table("/proposals")

st.subheader("Original tariff records")
if records_df.empty:
    st.info("Run Tariff Analysis to load records.")
else:
    st.dataframe(records_df, use_container_width=True, hide_index=True)

st.subheader("Proposed updates")
if proposals_df.empty:
    st.info("Run Tariff Analysis to generate proposals.")
else:
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        min_confidence = st.slider("Minimum confidence", 0.0, 1.0, 0.0, 0.05)
    with filter_col2:
        risk_options = sorted(proposals_df["risk_level"].dropna().unique().tolist())
        risk_filter = st.multiselect("Risk", risk_options, default=risk_options)
    with filter_col3:
        status_options = sorted(proposals_df["status"].dropna().unique().tolist())
        status_filter = st.multiselect("Status", status_options, default=status_options)

    filtered = proposals_df[
        (proposals_df["confidence_score"] >= min_confidence)
        & (proposals_df["risk_level"].isin(risk_filter))
        & (proposals_df["status"].isin(status_filter))
    ]
    st.dataframe(filtered, use_container_width=True, hide_index=True)

    record_names = (
        records_df.set_index("pack_id")["pack_name"].to_dict() if not records_df.empty else {}
    )
    for proposal in filtered.to_dict(orient="records"):
        title = (
            f"{record_names.get(proposal['pack_id'], proposal['pack_id'])} | "
            f"{proposal['field_name']}"
        )
        with st.expander(title):
            metric_cols = st.columns(4)
            metric_cols[0].metric("Old value", str(proposal.get("old_value")))
            metric_cols[1].metric("Proposed value", str(proposal.get("proposed_value")))
            metric_cols[2].metric("Confidence", f"{proposal.get('confidence_score', 0):.2f}")
            metric_cols[3].metric("Risk", proposal.get("risk_level", ""))
            st.write(proposal.get("reasoning_summary", ""))
            st.write("Evidence sources:", ", ".join(proposal.get("evidence_sources") or []))
            action_cols = st.columns(2)
            if action_cols[0].button(
                "Approve",
                key=f"approve-{proposal['pack_id']}-{proposal['field_name']}",
                use_container_width=True,
            ):
                api_request(
                    "POST",
                    "/review",
                    json={
                        "pack_id": proposal["pack_id"],
                        "field_name": proposal["field_name"],
                        "decision": "approved",
                        "reviewer": "streamlit_demo",
                        "reasoning": "Approved in Streamlit review UI.",
                    },
                )
                st.rerun()
            if action_cols[1].button(
                "Reject",
                key=f"reject-{proposal['pack_id']}-{proposal['field_name']}",
                use_container_width=True,
            ):
                api_request(
                    "POST",
                    "/review",
                    json={
                        "pack_id": proposal["pack_id"],
                        "field_name": proposal["field_name"],
                        "decision": "rejected",
                        "reviewer": "streamlit_demo",
                        "reasoning": "Rejected in Streamlit review UI.",
                    },
                )
                st.rerun()

st.subheader("Downloads")
download_cols = st.columns(3)
with download_cols[0]:
    render_download(
        "updated_tariff_packs.xlsx",
        OUTPUT_DIR / "updated_tariff_packs.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
with download_cols[1]:
    render_download("audit_log.json", OUTPUT_DIR / "audit_log.json", "application/json")
with download_cols[2]:
    render_download("review_report.md", OUTPUT_DIR / "review_report.md", "text/markdown")
