from typing import Any

from google.adk.agents import LlmAgent
from google.adk.agents.context import Context
from google.adk.workflow import FunctionNode, Workflow

from app import metrics, security, workorders_reader
from app.config import LLM_MODEL, WORKORDERS_PATH, WORKORDERS_SHEET_NAME
from app.models import MetricsReport, NarrativeOutput, WorkOrder

# ---------------------------------------------------------------------------
# Node 1 — fetch_workorders
# ---------------------------------------------------------------------------
# The trigger message (node_input) is ignored — this is an "ambient" agent
# meant to be run on a schedule ("generate this week's report"), not one that
# takes structured user input like the expense-approval agent did.


def fetch_workorders(ctx: Context, node_input: Any) -> list[WorkOrder]:
    workorders = workorders_reader.fetch_workorders(
        path=WORKORDERS_PATH, sheet_name=WORKORDERS_SHEET_NAME
    )
    ctx.state["total_ordenes_leidas"] = len(workorders)
    return workorders


# ---------------------------------------------------------------------------
# Node 2 — screen_notes (security boundary)
# ---------------------------------------------------------------------------


def screen_notes(ctx: Context, node_input: list[WorkOrder]) -> list[WorkOrder]:
    cleaned, flagged = security.screen_notes(node_input)
    ctx.state["notas_filtradas_por_seguridad"] = flagged
    return cleaned


# ---------------------------------------------------------------------------
# Node 3 — compute_metrics
# ---------------------------------------------------------------------------


def compute_metrics_node(ctx: Context, node_input: list[WorkOrder]) -> MetricsReport:
    report = metrics.compute_metrics(node_input)
    ctx.state["metrics_report"] = report.model_dump()
    return report


# ---------------------------------------------------------------------------
# Node 4 — generate_narrative (LLM)
# ---------------------------------------------------------------------------
# Receives only the aggregated MetricsReport — never the raw work orders, so
# per-order free text (already screened in node 2) never reaches the model.

generate_narrative = LlmAgent(
    name="generate_narrative",
    model=LLM_MODEL,
    instruction=(
        "Eres un ingeniero de mantenimiento senior en una planta farmacéutica. "
        "Se te da un informe agregado de métricas semanales de mantenimiento "
        "(horas de parada por equipo, coste por tipo de intervención, y "
        "órdenes GMP-críticas vencidas). Escribe un resumen breve (2-3 frases) "
        "en español y entre 1 y 3 recomendaciones accionables, priorizando "
        "siempre cualquier orden GMP-crítica vencida. Sé concreto y cita "
        "equipos/órdenes por su identificador cuando sea relevante."
    ),
    output_schema=NarrativeOutput,
    output_key="narrative",
)

# ---------------------------------------------------------------------------
# Graph wiring
# ---------------------------------------------------------------------------

_fetch = FunctionNode(func=fetch_workorders, name="fetch_workorders")
_screen = FunctionNode(func=screen_notes, name="screen_notes")
_metrics_node = FunctionNode(func=compute_metrics_node, name="compute_metrics")

root_agent = Workflow(
    name="maintenance_insights",
    edges=[
        ("START", _fetch),
        (_fetch, _screen),
        (_screen, _metrics_node),
        (_metrics_node, generate_narrative),
    ],
)
