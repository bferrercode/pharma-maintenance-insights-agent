import logging

from dotenv import load_dotenv

# Must run before `app.agent` is imported: that import chain builds the
# LlmAgent, which reads GOOGLE_API_KEY from the environment.
load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import root_agent
from app.models import MaintenanceInsights, MetricsReport, NarrativeOutput

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_APP_NAME = "maintenance_insights"
_USER_ID = "dashboard"

app = FastAPI(title="pharma-maintenance-insights-agent")

_session_service = InMemorySessionService()
_runner = Runner(agent=root_agent, session_service=_session_service, app_name=_APP_NAME)


async def _run_workflow() -> MaintenanceInsights:
    """Runs the ADK Workflow end to end and reads the final session state.

    Each node writes its structured output into ctx.state (same pattern as
    ambient-expense-agent's expense/risk_assessment), so instead of parsing
    the streamed events we just read the state back after the run completes.
    """
    session = await _session_service.create_session(app_name=_APP_NAME, user_id=_USER_ID)
    message = types.Content(
        role="user",
        parts=[types.Part.from_text(text="Genera el informe semanal de mantenimiento.")],
    )

    events = list(
        _runner.run(
            new_message=message,
            user_id=_USER_ID,
            session_id=session.id,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        )
    )
    if not events:
        raise RuntimeError("El workflow no produjo ningún evento")

    final_session = await _session_service.get_session(
        app_name=_APP_NAME, user_id=_USER_ID, session_id=session.id
    )
    state = final_session.state

    return MaintenanceInsights(
        metrics=MetricsReport(**state["metrics_report"]),
        narrativa=NarrativeOutput(**state["narrative"]),
        notas_filtradas_por_seguridad=state.get("notas_filtradas_por_seguridad", []),
    )


@app.get("/api/insights/weekly", response_model=MaintenanceInsights)
async def weekly_insights() -> MaintenanceInsights:
    return await _run_workflow()


# Serves static/index.html (dashboard) at "/". Mounted last so it doesn't
# shadow the /api routes above.
app.mount("/", StaticFiles(directory="static", html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
