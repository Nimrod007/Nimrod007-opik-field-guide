"""The Pydantic AI agent: scheduling email in, CalendarEvent out."""

from pydantic_ai import Agent

from .schema import CalendarEvent, Email, render_email

MODEL = "openai:gpt-4o-mini"

SYSTEM_PROMPT = (
    "You extract one calendar event from a scheduling email. Resolve relative "
    "days ('Thursday', 'this coming Friday') against the sent date given at the "
    "top. If a message was corrected or moved, use the latest plan. Fill in "
    "only what the email actually says: if a date, time, place or link is not "
    "stated, leave it null - never guess or invent values."
)


def build_agent(model: str = MODEL) -> Agent[None, CalendarEvent]:
    return Agent(model, output_type=CalendarEvent, system_prompt=SYSTEM_PROMPT)


def extract_event(agent: Agent[None, CalendarEvent], email: Email) -> dict:
    """One extraction: returns the event as a JSON-ready dict."""
    result = agent.run_sync(render_email(email))
    return result.output.model_dump(mode="json")
