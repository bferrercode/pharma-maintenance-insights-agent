import datetime
from pathlib import Path

import openpyxl

from app.models import WorkOrder

# Expected header row, in this exact order (see .env.example / README for the
# workbook template). Kept explicit rather than trusting the header row
# as-is, so a renamed/reordered column fails loudly instead of silently
# misparsing.
_EXPECTED_HEADERS = [
    "orden", "equipo", "tipo", "fecha", "horas_parada",
    "coste", "criticidad_gmp", "estado", "notas",
]


def _coerce_fecha(value: object) -> str:
    if isinstance(value, datetime.datetime):
        return value.date().isoformat()
    if isinstance(value, datetime.date):
        return value.isoformat()
    return str(value)


def _coerce_numeric(value: object, *, campo: str, orden: str) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    raise ValueError(
        f"Orden {orden}: el campo '{campo}' deberia ser numerico pero la celda "
        f"contiene {value!r}. Revisa el formato de esa celda en el Excel "
        "(Excel suele autoformatear '1,5' como fecha si la columna quedo con "
        "formato de fecha)."
    )


def fetch_workorders(path: str, sheet_name: str | None = None) -> list[WorkOrder]:
    """Read the mock SAP-PM-style work-order export (an .xlsx, mirroring how a
    maintenance planner would actually pull a work-order list out of SAP PM)
    into typed WorkOrder records.

    Swap this function alone to later read from a real SAP PM OData export
    instead — nothing else in the agent depends on how the data got here.
    """
    workbook_path = Path(path)
    if not workbook_path.exists():
        raise FileNotFoundError(f"No se encuentra el workbook de ordenes: {workbook_path}")

    workbook = openpyxl.load_workbook(workbook_path, data_only=True)
    worksheet = workbook[sheet_name] if sheet_name else workbook.active

    rows = list(worksheet.iter_rows(values_only=True))
    if not rows:
        return []

    header, *data_rows = rows
    header = [str(h).strip() for h in header]
    if header != _EXPECTED_HEADERS:
        raise ValueError(f"Cabecera {header!r} no coincide con la esperada {_EXPECTED_HEADERS!r}")

    workorders = []
    for row in data_rows:
        record = dict(zip(header, row))
        orden = str(record["orden"])
        workorders.append(
            WorkOrder(
                orden=orden,
                equipo=str(record["equipo"]),
                tipo=str(record["tipo"]),
                fecha=_coerce_fecha(record["fecha"]),
                horas_parada=_coerce_numeric(record["horas_parada"], campo="horas_parada", orden=orden),
                coste=_coerce_numeric(record["coste"], campo="coste", orden=orden),
                criticidad_gmp=str(record["criticidad_gmp"]).strip().lower() in ("si", "sí", "true", "yes"),
                estado=str(record["estado"]),
                notas=str(record["notas"] or ""),
            )
        )
    return workorders
