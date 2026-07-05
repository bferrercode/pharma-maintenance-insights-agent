import re

from app.models import WorkOrder

# Adapted from ambient-expense-agent's _INJECTION_PATTERNS (Day 4 concept):
# the free-text `notas` field is technician-entered text (mirroring a SAP PM
# long-text field) and is the only part of a work order an external party
# could use to smuggle instructions to the LLM. Everything else is
# structured/typed data, so this is the one node that needs a trust boundary.
_INJECTION_PATTERNS = re.compile(
    r"(ignore|bypass|override|forget|disregard).{0,30}(rule|instruction|policy|threshold)|"
    r"(ignora|omite|anula|olvida).{0,30}(regla|instruccion|instrucción|política)|"
    r"auto[\s-]?aprob|siempre aprob|debes aprob",
    re.IGNORECASE,
)

_REDACTED_PLACEHOLDER = "[NOTA FILTRADA POR SEGURIDAD]"


def screen_notes(workorders: list[WorkOrder]) -> tuple[list[WorkOrder], list[str]]:
    """Strip suspected prompt-injection text from `notas` before it can reach
    the narrative LLM node. Returns (cleaned_workorders, flagged_order_ids).
    """
    cleaned: list[WorkOrder] = []
    flagged: list[str] = []

    for wo in workorders:
        if wo.notas and _INJECTION_PATTERNS.search(wo.notas):
            flagged.append(wo.orden)
            wo = wo.model_copy(update={"notas": _REDACTED_PLACEHOLDER})
        cleaned.append(wo)

    return cleaned, flagged
