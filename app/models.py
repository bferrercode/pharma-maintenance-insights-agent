from pydantic import BaseModel


class WorkOrder(BaseModel):
    """One row of the mock SAP-PM-style work-order sheet."""

    orden: str
    equipo: str
    tipo: str  # "Preventivo" | "Correctivo" | "Calibracion"
    fecha: str  # ISO date, e.g. "2026-06-29"
    horas_parada: float
    coste: float
    criticidad_gmp: bool
    estado: str  # "Abierta" | "Cerrada" | "Vencida"
    notas: str = ""


class MetricsReport(BaseModel):
    """Aggregated, identity-free metrics — no work order includes patient/
    operator names in this project, but this is still the single point where
    raw records collapse into numbers, so it's the boundary any future PII
    field would also have to cross."""

    total_ordenes: int
    horas_parada_totales: float
    horas_parada_por_equipo: dict[str, float]
    coste_total: float
    coste_por_tipo: dict[str, float]
    ordenes_gmp_vencidas: int
    detalle_gmp_vencidas: list[str]  # order IDs only


class NarrativeOutput(BaseModel):
    """Structured output of the LLM narrative node."""

    resumen: str
    recomendaciones: list[str]


class MaintenanceInsights(BaseModel):
    """Final shape returned by the API / rendered on the dashboard."""

    metrics: MetricsReport
    narrativa: NarrativeOutput
    notas_filtradas_por_seguridad: list[str]  # order IDs whose notas were screened
