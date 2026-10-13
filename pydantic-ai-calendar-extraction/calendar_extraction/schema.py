"""The typed record the agent must return, and the corpus it is run over."""

import datetime as dt
import json
from pathlib import Path

from pydantic import BaseModel, Field

DATA_FILE = Path(__file__).parent.parent / "data" / "emails.json"


class CalendarEvent(BaseModel):
    """One calendar event pulled out of a scheduling email."""

    title: str = Field(description="Short event title")
    date: dt.date | None = Field(None, description="Calendar date, only if the email pins one down")
    start_time: dt.time | None = Field(None, description="Local start time, only if stated")
    end_time: dt.time | None = Field(
        None, description="End time, only if stated or derivable from a stated duration"
    )
    timezone: str | None = Field(None, description="Timezone as written in the email, if any")
    location: str | None = Field(None, description="Physical place, only if stated")
    meeting_url: str | None = Field(None, description="Video-call link, only if present")
    attendees: list[str] = Field(default_factory=list, description="People named as participants")


class Email(BaseModel):
    """One fictional scheduling email plus the plain-language checks for its extraction."""

    id: str
    sent: dt.date
    text: str
    assertions: list[str] = Field(default_factory=list)


def load_emails(path: Path = DATA_FILE) -> list[Email]:
    return [Email(**row) for row in json.loads(path.read_text())]


def render_email(email: Email) -> str:
    """The agent's input: the body plus the sent date, so 'Thursday' can be resolved."""
    return f"Email sent on {email.sent.isoformat()} ({email.sent:%A}).\n\n{email.text}"
