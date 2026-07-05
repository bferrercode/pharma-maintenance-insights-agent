import os

# Region + Vertex config must be set BEFORE importing the agent, same
# constraint as ambient-expense-agent: gemini-2.5-flash needs a real region,
# not "global", for the Agent Engine Sessions API to agree with the model.
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "europe-west1")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")

import vertexai
from vertexai.preview.reasoning_engines import AdkApp

from app.agent import root_agent

project = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
location = os.environ.get("GOOGLE_CLOUD_LOCATION", "europe-west1")

vertexai.init(project=project, location=location)

agent_runtime = AdkApp(
    agent=root_agent,
    enable_tracing=True,
)
