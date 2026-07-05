from app.config import GMP_OVERDUE_ESTADO
from app.models import MetricsReport, WorkOrder

# Cost is only counted once a work order is finished (Cerrada) or expired
# unresolved (Vencida) — an "Abierta" order's final cost isn't settled yet.
_COST_COUNTED_STATES = {"Cerrada", "Vencida"}


def compute_metrics(workorders: list[WorkOrder]) -> MetricsReport:
    horas_parada_por_equipo: dict[str, float] = {}
    coste_por_tipo: dict[str, float] = {}
    coste_total = 0.0
    detalle_gmp_vencidas: list[str] = []

    for wo in workorders:
        horas_parada_por_equipo[wo.equipo] = (
            horas_parada_por_equipo.get(wo.equipo, 0.0) + wo.horas_parada
        )

        if wo.estado in _COST_COUNTED_STATES:
            coste_total += wo.coste
            coste_por_tipo[wo.tipo] = coste_por_tipo.get(wo.tipo, 0.0) + wo.coste

        if wo.criticidad_gmp and wo.estado == GMP_OVERDUE_ESTADO:
            detalle_gmp_vencidas.append(wo.orden)

    return MetricsReport(
        total_ordenes=len(workorders),
        horas_parada_totales=sum(horas_parada_por_equipo.values()),
        horas_parada_por_equipo=horas_parada_por_equipo,
        coste_total=coste_total,
        coste_por_tipo=coste_por_tipo,
        ordenes_gmp_vencidas=len(detalle_gmp_vencidas),
        detalle_gmp_vencidas=detalle_gmp_vencidas,
    )
