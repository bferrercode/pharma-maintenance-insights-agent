# Pharma Maintenance Insights Agent

Kaggle "5-Day AI Agents: Intensive Vibe Coding Course with Google" — capstone project (track: **Agents for Business**).

## Problem

In a pharma plant, maintenance data (work orders, downtime, cost, GMP-critical
equipment status) lives in **SAP PM** but rarely gets turned into a digestible
weekly picture without someone manually pulling and summarizing it. Idle/downtime
hours and overdue GMP-critical maintenance are both money and compliance risk,
and they're easy to miss buried in a raw work-order list.

## Solution

An ADK agent that reads a week of work orders, computes maintenance KPIs, and
writes a short natural-language summary with recommendations — served on a
one-page dashboard.

**Data source note:** this demo reads a standalone `.xlsx` file (`OT SAP PM
Demo.xlsx`) with the same column shape a real SAP PM work-order export would
have — in practice, a maintenance planner exporting a work-order list out of
SAP PM often ends up with exactly this kind of Excel file. No real
plant/company system or data is used anywhere in this project. In a production
setup, `app/workorders_reader.py` would be replaced by a call to SAP PM's
OData service (or an IW38/IW68 extract) — nothing else in the agent would
need to change, since every other node only depends on the `WorkOrder` shape.

## Architecture

Single ADK `Workflow` (`app/agent.py`):

```
START → fetch_workorders → screen_notes → compute_metrics → generate_narrative → END
        (Sheets API)       (security)      (pure Python)     (Gemini LLM)
```

1. **fetch_workorders** — reads the mock `.xlsx` work-order export with
   `openpyxl` (`app/workorders_reader.py`).
2. **screen_notes** — the free-text `notas` field (what a technician would
   type into SAP PM) is the one part of a work order an outside party could
   use to smuggle instructions to the LLM. This node screens it for
   prompt-injection patterns and redacts anything suspicious *before* it can
   reach node 4. Adapted from the PII/injection screening built in this
   course's Day 4 expense-approval agent.
3. **compute_metrics** — pure functions (`app/metrics.py`) computing downtime
   hours per equipment, cost per maintenance type, and overdue GMP-critical
   orders. Produces an aggregated `MetricsReport` — no per-order free text
   passes beyond this point.
4. **generate_narrative** — an `LlmAgent` (Gemini) that only ever sees the
   aggregated `MetricsReport`, never raw work orders, and writes a short
   weekly summary + recommendations in Spanish.

A FastAPI app (`app/fast_api_app.py`) runs the Workflow through ADK's
`Runner`/`InMemorySessionService` and serves the result as JSON at
`GET /api/insights/weekly`; a static dashboard (`static/index.html`, vanilla
JS + Chart.js) renders it: KPI cards, two charts (downtime/equipment,
cost/type), and the narrative.

## Course concepts demonstrated

| Concept | Where |
|---|---|
| Agent (ADK Workflow, multi-node graph) | `app/agent.py` |
| Security features (prompt-injection screening before the LLM node) | `app/security.py`, `app/agent.py` (`screen_notes`) |
| Agent skills / Agents CLI | `agents-cli playground` for interactive testing (see below); `agents-cli-manifest.yaml` |

## Setup

1. `uv sync --group dev`
2. Copy `.env.example` to `.env` and fill in `GOOGLE_API_KEY` (Gemini API key,
   AI Studio). `WORKORDERS_PATH`/`WORKORDERS_SHEET_NAME` default to
   `OT SAP PM Demo.xlsx` / `Hoja 1` in the project root — only override if you
   rename or move the file.
3. This repo already includes a sample `OT SAP PM Demo.xlsx` in the project
   root (synthetic data, header row: `orden | equipo | tipo | fecha |
   horas_parada | coste | criticidad_gmp | estado | notas`). Swap it for your
   own file with the same header to try different data.
4. Run the tests: `uv run pytest tests/unit`
5. Run the dashboard: `uv run uvicorn app.fast_api_app:app --reload`, open
   `http://localhost:8000`
6. Interactive agent check: `agents-cli playground`

## Scope

This project deliberately concentrates effort on three things — a multi-node
ADK agent, a concrete security boundary (prompt-injection screening ahead of
the LLM), and a working local demo — rather than spreading it across every
possible integration:

- **Deployment.** The agent is deployment-ready as-is: `agents-cli-manifest.yaml`
  and `app/agent_runtime_app.py` wrap it for Vertex AI Agent Engine with no
  further changes. This submission runs it locally, since a live cloud
  endpoint doesn't change how the agent reasons or is architected.
- **Data source.** It reads a mock SAP-PM-shaped Excel export rather than a
  live SAP PM connection, since the interesting part to demonstrate is the
  insight pipeline, not an ERP integration. `app/workorders_reader.py` is the
  single, isolated seam that a real SAP PM OData integration would replace.
- **Tooling.** The agent's reasoning layer is entirely ADK-native (no MCP
  server or Antigravity integration in this build).
