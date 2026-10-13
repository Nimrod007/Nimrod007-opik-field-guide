"""Shared settings and environment loading."""

import os
import pathlib

# Every trace, and the test suite itself, is filed under this Opik project.
PROJECT_NAME = "llamaindex-syllabus-pdf-qa"
SUITE_NAME = "llamaindex-syllabus-policy-suite"

ROOT = pathlib.Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "data" / "syllabi"

LLM_MODEL = "gpt-4o-mini"
EMBED_MODEL = "text-embedding-3-small"
TOP_K = 4


def load_env() -> None:
    """Pick the Opik project and load OPENAI_API_KEY from a nearby .env, if any."""
    # Must be set before Opik creates its client, or traces land in "Default Project".
    os.environ.setdefault("OPIK_PROJECT_NAME", PROJECT_NAME)
    import dotenv

    for folder in (ROOT, *ROOT.parents[:2]):
        dotenv.load_dotenv(folder / ".env")
