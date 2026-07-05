import os
from pathlib import Path

# Gemini model used by the narrative-generation node.
LLM_MODEL = "gemini-2.5-flash"

# Mock "SAP PM style" work-order export (see README). In a real plant this
# would come from SAP PM (an OData service or an IW38/IW68 export) — this
# agent only depends on the WorkOrder shape, so swapping the source later
# means replacing app/workorders_reader.py, nothing else.
_REPO_ROOT = Path(__file__).resolve().parents[1]
WORKORDERS_PATH = os.environ.get("WORKORDERS_PATH", str(_REPO_ROOT / "OT SAP PM Demo.xlsx"))
WORKORDERS_SHEET_NAME = os.environ.get("WORKORDERS_SHEET_NAME", "Hoja 1")

# A work order counts as an overdue GMP-critical order when criticidad_gmp is
# True and estado == "Vencida".
GMP_OVERDUE_ESTADO = "Vencida"
