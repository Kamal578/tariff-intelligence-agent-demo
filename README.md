# Tariff Intelligence Agent Demo

Synthetic technical-interview demo of an enterprise tariff remediation workflow. Analysts start with an Excel tariff file, the agent detects bad rows, searches mock enterprise sources, proposes structured updates with evidence, routes changes to human review, and writes only approved updates to a new Excel workbook.

No real company data is included. No real Confluence, Gmail, IMAP, Atlassian, or enterprise connector is used.

## Business Problem

Telecom reporting teams often maintain tariff and pack data in Excel. Missing prices, stale pack names, retired products, invalid activation codes, and conflicting status values can break downstream reporting. In a real enterprise setting, analysts would manually search Confluence, wiki notes, and email announcements before correcting the file. This demo simulates that workflow with local mock sources and a human-in-the-loop approval gate.

## Architecture

```mermaid
flowchart LR
    Excel["Excel tariff_packs.xlsx"] --> Detect["Deterministic issue detection"]
    Detect --> Query["Issue-aware search queries"]
    Sources["Mock Confluence / Wiki / Inbox JSON"] --> Connectors["Local mock connector router"]
    Query --> Connectors
    Connectors --> Evidence["Ranked evidence + conflicts"]
    Evidence --> LLM["Gemini JSON proposal or fallback"]
    LLM --> Pydantic["Pydantic validation"]
    Pydantic --> Jobs["Analysis job + run history"]
    Jobs --> API["FastAPI review API"]
    API --> React["React analyst dashboard"]
    React --> Review["Approve / reject"]
    Review --> Output["Updated Excel + audit_log.json + report.md"]
```

## Demo Workflow

1. Start the FastAPI backend.
2. Start the React dashboard.
3. Select **Quick Preview** for deterministic local proposals or **Gemini** for live LLM proposals, then click **Run Analysis**.
4. Review original Excel records, generated proposals, confidence, risk, and conflict badges.
5. Open a proposal and inspect Confluence/wiki/email evidence cards.
6. Use mock source search for queries like `YouthMax 10GB price` or `Student Social discontinued`.
7. Approve or reject individual proposals.
8. Click **Apply Approved Updates**.
9. Download `updated_tariff_packs.xlsx`, `audit_log.json`, `report.md`, or the full run package ZIP.

## Production-Style Workflow Features

- Job-based analysis runs with persisted status, stage, progress, timestamps, requested mode, actual mode, and errors.
- Dashboard sidebar with dedicated views for metrics, analysis runs, review queue, sources, audit/downloads, and runtime settings.
- Runtime readiness checks for backend status, Gemini configuration, source counts, and mock connector safety.
- Proposal review filters for risk, status, confidence, conflicts, and free-text pack/field search.
- Field-level proposal diff showing current Excel value versus proposed value.
- Evidence traceability summary showing source authority, freshness, conflicts, and approved/deprecated source counts.
- Analyst review comments are stored with approve/reject decisions.
- Applied proposals move to `applied` after approved Excel mutations are written.
- Exportable run package ZIP for handoff and interview inspection.

## Mock Sources

Mock sources live in `data/mock_sources/`:

- `confluence_pages.json`: 10 approved/deprecated/draft product pages.
- `wiki_pages.json`: 7 operational rule and team-note pages.
- `inbox_emails.json`: 8 synthetic update emails.
- `source_metadata.json`: counts and mock-source metadata.

These files intentionally include conflicts:

- YouthMax 10GB old price `11.90 AZN` vs approved `12.90 AZN`.
- Business Pro 25GB renamed to Business Pro Plus.
- Night Owl 5GB old activation code `*123*50#` vs approved `*123*55#`.
- Student Social 3GB discontinued after older active notes.
- Family Data 18GB replaced by Family Share 20GB.
- Roaming Lite 1GB draft `10` minutes vs approved `20` minutes.

Mock sources are used because this is an interview-safe synthetic demo. Real connectors would require credentials, permissions, source-level ACLs, rate-limit handling, and confidential data controls that do not belong in a portable demo.

## Run Locally

Docker Compose:

```bash
# Optional: configure Gemini for the backend container
cp .env.docker.example .env.docker
# edit .env.docker and set GEMINI_API_KEY if desired

docker compose up --build
```

Open:

```text
Backend:  http://127.0.0.1:8000
Frontend: http://127.0.0.1:5173
```

The Compose stack runs:

- `backend`: FastAPI/Uvicorn on port `8000`.
- `frontend`: built React app served by Nginx on port `5173`.

Generated artifacts are mounted to the host at `data/output/`, so downloaded Excel, audit JSON, and report files remain inspectable after the containers stop.

Useful Docker commands:

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f frontend
docker compose down
```

Local Python/Node workflow:

Backend:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Optional: add GEMINI_API_KEY to .env
uvicorn app.main:app --reload
```

React frontend:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
Backend:  http://127.0.0.1:8000
Frontend: http://127.0.0.1:5173
```

Optional custom API URL:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8001 npm run dev
```

Streamlit fallback/dev UI remains available:

```bash
streamlit run ui/streamlit_app.py
```

## API Endpoints

- `GET /health`
- `GET /config/status`
- `POST /analysis-jobs`
- `GET /analysis-jobs`
- `GET /analysis-jobs/{job_id}`
- `POST /analysis-jobs/{job_id}/cancel`
- `GET /records`
- `POST /process` with `{"mode": "preview"}` or `{"mode": "gemini"}`
- `GET /proposals`
- `GET /proposals/{proposal_id}`
- `POST /review`
- `POST /apply-approved`
- `GET /audit-log`
- `GET /report`
- `GET /download/updated-excel`
- `GET /download/audit-json`
- `GET /download/report-md`
- `GET /download/run-package`
- `GET /sources/search?q=YouthMax%2010GB%20price`
- `GET /sources/stats`
- `POST /reset-demo`

## Analysis Modes

The React dashboard has two run modes:

- **Quick Preview** sends `{"mode": "preview"}` and never calls Gemini. It uses deterministic local proposal generation with retrieved mock evidence.
- **Gemini** sends `{"mode": "gemini"}` and attempts live Gemini proposal generation. If Gemini is unavailable, the backend falls back to deterministic proposals.

The API response `mode` reports what actually happened: `preview`, `gemini`, `fallback`, or `mixed`.

## Gemini and Fallback Mode

Gemini support uses `google-genai` and reads:

```text
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
```

If `GEMINI_API_KEY` is missing or the model response is invalid while Gemini mode is selected, deterministic fallback logic still generates valid `ProposedUpdate` objects using synthetic reference values and retrieved mock evidence. The full dashboard, approval flow, Excel output, audit log, and tests work offline.

## Technical Decisions

- Excel mirrors real analyst workflows and makes the before/after artifact easy to inspect.
- Mock connectors keep the demo local and interview-safe while making source retrieval explicit.
- Evidence ranking boosts exact pack matches, freshness, approved Confluence pages, and source priority.
- Pydantic enforces structured proposals before they enter review.
- Human approval is required before any Excel output is written.
- React is the primary demo UI; Streamlit remains a quick dev fallback.
- Local JSON state keeps the project lightweight: `data/output/proposals.json`, `review_decisions.json`, `analysis_runs.json`, `audit_log.json`, `report.md`, `analysis_run_package.zip`, and `updated_tariff_packs.xlsx`.

## Trade-Offs

- The search layer is deterministic keyword ranking, not semantic search, so behavior is explainable but less flexible than production retrieval.
- State is file-based rather than transactional.
- The fallback proposal engine is intentionally rule-driven for demo reliability.
- Authentication and source permissions are omitted because all sources are synthetic local files.

## Production Improvements

- Real Confluence API connector.
- Gmail or Microsoft Graph connector.
- Auth/RBAC and source-level permissions.
- Postgres persistence.
- Replace in-process background jobs with a durable queue such as Celery/RQ/Temporal.
- Observability, tracing, and prompt/version telemetry.
- Evaluation datasets for proposal quality.
- Analyst feedback loop for continuous improvement.
- Docker/Kubernetes deployment.
- CI/CD security scanning and dependency governance.

## Tests

```bash
python -m pytest
cd frontend && npm run build
docker compose config
docker compose up --build
```

Current tests cover issue detection, mock connector search, evidence ranking, source conflict detection, proposal validation, analysis run history, review decisions, approved-only Excel updates, applied proposal status, and package export.

## Three-Minute Demo Script

1. Show `data/input/tariff_packs.xlsx` and point out rows with old prices, missing activation codes, discontinued packs, and duplicate names.
2. Open the React dashboard, keep **Quick Preview** selected for the fast offline path, and click **Run Analysis**.
3. Show metrics: total records, issues, generated proposals, high-risk proposals, approved/rejected counts, and source conflicts.
4. Open the YouthMax 10GB price proposal. Highlight old value `11.90`, proposed value `12.90`, conflict badge, and evidence cards showing old draft vs approved sources.
5. Use source search for `Student Social discontinued` to show the agent is searching mock enterprise evidence rather than guessing.
6. Approve one low-risk proposal and reject one conflicting proposal.
7. Click **Apply Approved Updates** and download the updated Excel plus audit/report artifacts.
