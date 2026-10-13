"""Shared setup imported first by every process (client and worker)."""

import os
from pathlib import Path

from dotenv import load_dotenv

TASK_QUEUE = "temporal-py-grant-review"
PROJECT = "temporal-py-grant-review"
MODEL = "gpt-4o-mini"

# Load a local .env, then the repo-root one (the first value found wins).
load_dotenv()
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# Traces from the client and the worker are separate OS processes; both must name the
# same Opik project or the one trace would split across two projects.
os.environ.setdefault("OPIK_PROJECT_NAME", PROJECT)

TEMPORAL_ADDRESS = os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")
