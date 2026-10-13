"""PII redaction pipeline: regex pre-pass -> LLM detection -> merge -> redact -> verify."""

from __future__ import annotations

import json
import re

MODEL = "gpt-4o-mini"

PATTERNS = {
    "EMAIL": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+\w"),
    "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "CARD": re.compile(r"\b(?:\d{4}[ -]){3}\d{4}\b"),
    "PHONE": re.compile(r"(?:\+\d{1,3} ?)?(?:\(\d{3}\) ?\d{3}-\d{4}|\d{2} \d{4} \d{4})"),
    "IP": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
}

SYSTEM_PROMPT = (
    "You find personal data in a document that simple patterns cannot catch: "
    "person names (including first names alone), street addresses, dates of birth, "
    "and home towns. Ignore emails, phone numbers, card numbers, SSNs and IPs. "
    'Reply with JSON: {"items": [{"text": "<exact substring>", "label": "NAME|ADDRESS|DOB|PLACE"}]}. '
    "Each text must be copied verbatim from the document. If there is none, return an empty list."
)


def regex_prepass(text: str) -> list[dict]:
    """Cheap, deterministic detection of well-formed identifiers."""
    found = []
    for label, pattern in PATTERNS.items():
        for m in pattern.finditer(text):
            found.append({"text": m.group(0), "label": label, "source": "regex"})
    return found


def build_messages(text: str) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": text},
    ]


def parse_llm_items(raw: str, text: str) -> list[dict]:
    """Parse the model's JSON; keep only spans that really occur in the document."""
    try:
        items = json.loads(raw).get("items", [])
    except (json.JSONDecodeError, AttributeError):
        return []
    out = []
    for it in items:
        if isinstance(it, dict) and isinstance(it.get("text"), str) and it["text"] in text:
            out.append({"text": it["text"], "label": str(it.get("label", "PII")).upper(), "source": "llm"})
    return out


def call_llm(client, text: str):
    """One chat completion; returns the raw OpenAI response object."""
    return client.chat.completions.create(
        model=MODEL,
        messages=build_messages(text),
        response_format={"type": "json_object"},
        temperature=0,
    )


def merge_findings(*groups: list[dict]) -> list[dict]:
    """Union of all findings; identical strings collapse, strings inside longer ones drop."""
    by_text: dict[str, dict] = {}
    for group in groups:
        for f in group:
            by_text.setdefault(f["text"], f)  # earlier groups (regex) win ties
    texts = list(by_text)
    return [by_text[t] for t in texts if not any(t != o and t in o for o in texts)]


def redact(text: str, findings: list[dict]) -> str:
    out = text
    for f in sorted(findings, key=lambda f: len(f["text"]), reverse=True):
        out = out.replace(f["text"], f"[{f['label']}]")
    return out


def verify(original_findings: list[dict], redacted: str) -> dict:
    """Re-scan the output: no found string may survive and the regexes must find nothing."""
    leaks = [f["text"] for f in original_findings if f["text"] in redacted]
    leaks += [f["text"] for f in regex_prepass(redacted)]
    return {"ok": not leaks, "leaks": leaks}


def score_recall(truth: list[str], redacted: str) -> dict:
    """Ground-truth check: how many known PII strings are gone from the output."""
    leaked = [t for t in truth if t in redacted]
    recall = 1.0 if not truth else (len(truth) - len(leaked)) / len(truth)
    return {"recall": recall, "leaked": leaked}


def process_document(client, doc: dict) -> dict:
    text = doc["text"]
    rx = regex_prepass(text)
    response = call_llm(client, text)
    llm = parse_llm_items(response.choices[0].message.content or "", text)
    merged = merge_findings(rx, llm)
    redacted = redact(text, merged)
    return {"redacted": redacted, "findings": merged, "verify": verify(merged, redacted),
            "score": score_recall(doc.get("pii", []), redacted)}
