"""A cheap, offline check for invented values: does the event only say what the email says?"""

import re

from .schema import Email


def _words(value: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9]+", value.lower()) if len(w) > 2]


def grounding_issues(email: Email, event: dict) -> list[str]:
    """Return one message per value in `event` that the email text cannot support."""
    text = email.text.lower()
    issues = []
    url = event.get("meeting_url")
    if url and url.lower() not in text:
        issues.append(f"meeting_url {url!r} is not in the email")
    location = event.get("location")
    if location and not any(w in text for w in _words(location)):
        issues.append(f"location {location!r} shares no words with the email")
    for name in event.get("attendees", []):
        if not any(w in text for w in _words(name)):
            issues.append(f"attendee {name!r} is not mentioned in the email")
    if not event.get("date") and (event.get("start_time") or event.get("end_time")):
        issues.append("a time was given without a date")
    return issues
