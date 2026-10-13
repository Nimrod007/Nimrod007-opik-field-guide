"""The post-mortem team: a planner, three investigators and a writer, wired as a LangGraph loop."""

import functools
import operator
from typing import Annotated, Literal

from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from postmortem.corpus import search_evidence

MAX_ROUNDS = 3
INVESTIGATORS = ("log_analyst", "timeline_builder", "change_reviewer")

# Which evidence files each investigator may read.
EVIDENCE = {
    "log_analyst": ["logs.md"],
    "timeline_builder": ["chat.md", "logs.md"],
    "change_reviewer": ["deploys.md", "chat.md"],
}
ROLES = {
    "log_analyst": "You are the log analyst. Report what the service logs show: errors, rates, latencies, exact times.",
    "timeline_builder": "You are the timeline builder. Produce a minute-by-minute sequence of what happened and who did what.",
    "change_reviewer": "You are the change-history reviewer. Identify which deploys or config changes could explain the incident, and how each was reviewed and gated.",
}



@functools.cache
def get_llm() -> ChatOpenAI:
    """Built on first use so importing the module (and the offline tests) needs no API key."""
    return ChatOpenAI(model="gpt-4o-mini", temperature=0)


class Finding(TypedDict):
    agent: str
    round: int
    focus: str
    answer: str
    sources: list[str]


class TeamState(TypedDict):
    incident: str
    round: int
    assignments: dict[str, str]  # investigator -> focus for the current round
    findings: Annotated[list[Finding], operator.add]
    ready: bool
    report: str


class Assignment(BaseModel):
    investigator: Literal["log_analyst", "timeline_builder", "change_reviewer"]
    focus: str = Field(description="One specific question for this investigator")


class PlannerDecision(BaseModel):
    """What the planner wants to happen next."""

    ready_to_write: bool = Field(description="True only when the evidence is sufficient and cross-checked")
    rationale: str = Field(description="One or two sentences explaining the decision")
    assignments: list[Assignment] = Field(
        default_factory=list, description="Investigations to run next round; empty if ready_to_write"
    )


def format_findings(findings: list[Finding]) -> str:
    return "\n\n".join(
        f"[round {f['round']}, {f['agent']}] Q: {f['focus']}\nA: {f['answer']}\n(sources: {', '.join(f['sources'])})"
        for f in findings
    )


def planner(state: TeamState) -> dict:
    """Round 1: assign each investigator a focus. Later rounds: review findings, then loop or hand off."""
    round_no = state.get("round", 0) + 1
    brief = (
        "You lead a post-mortem team. Evidence is split across service logs, an incident chat channel "
        "and deploy/config history. Investigators: log_analyst, timeline_builder, change_reviewer."
    )
    if round_no == 1:
        user = (
            f"Incident: {state['incident']}\n\nAssign each of the three investigators one broad opening "
            "question: the log_analyst on what failed, where and how badly; the timeline_builder on the "
            "full sequence of detection, diagnosis and recovery; the change_reviewer on what changed "
            "shortly before the incident and how it was reviewed and gated. Set ready_to_write to false."
        )
    else:
        user = (
            f"Incident: {state['incident']}\n\nFindings so far:\n{format_findings(state['findings'])}\n\n"
            "Review rule: a post-mortem is ready only when (a) the root cause is corroborated by at least "
            "two different evidence types (logs, chat, deploy history), and (b) it explains why recovery "
            "took as long as it did. If a hypothesis is single-sourced or something is unexplained, assign "
            "follow-up questions that name the specific change, time, or component to check, only to the "
            "investigators who can answer them, never repeat a question already answered, and set "
            "ready_to_write to false. Otherwise set ready_to_write to true."
        )
        if round_no > MAX_ROUNDS:
            user += "\n\nThe round budget is spent: set ready_to_write to true."
    decision = get_llm().with_structured_output(PlannerDecision).invoke([("system", brief), ("user", user)])
    ready = decision.ready_to_write or round_no > MAX_ROUNDS or not decision.assignments
    return {
        "round": round_no,
        "ready": ready,
        "assignments": {a.investigator: a.focus for a in decision.assignments},
    }


def make_investigator(name: str):
    def investigate(state: TeamState) -> dict:
        focus = state["assignments"].get(name)
        if not focus:  # nothing assigned this round: pass through without an LLM call
            return {}
        hits = search_evidence(focus, EVIDENCE[name], k=6)
        excerpts = "\n\n---\n\n".join(f"[{h['source']} / {h['heading']}]\n{h['text']}" for h in hits)
        reply = get_llm().invoke([
            ("system",
             f"{ROLES[name]} Use only the excerpts below. Quote exact times, numbers and names, and cite "
             f"the file for each claim. If the excerpts do not answer, say so.\n\n{excerpts}"),
            ("user", focus),
        ])
        finding: Finding = {
            "agent": name,
            "round": state["round"],
            "focus": focus,
            "answer": reply.content,
            "sources": sorted({h["source"] for h in hits}),
        }
        return {"findings": [finding]}

    return investigate


def route_after_planner(state: TeamState) -> Literal["log_analyst", "writer"]:
    return "writer" if state["ready"] else "log_analyst"


def writer(state: TeamState) -> dict:
    """Turn all investigation rounds into a blameless post-mortem."""
    reply = get_llm().invoke([
        ("system",
         "You are the writer. Write a blameless post-mortem in markdown with sections: Summary, Impact, "
         "Timeline (UTC), Root cause, Contributing factors, What went well, Action items. Use only the "
         "findings below; keep times, numbers and file citations accurate. Under 500 words.\n\n"
         + format_findings(state["findings"])),
        ("user", state["incident"]),
    ])
    return {"report": reply.content}


def build_graph() -> StateGraph:
    g = StateGraph(TeamState)
    g.add_node("planner", planner)
    for name in INVESTIGATORS:
        g.add_node(name, make_investigator(name))
    g.add_node("writer", writer)
    g.add_edge(START, "planner")
    g.add_conditional_edges("planner", route_after_planner, ["log_analyst", "writer"])
    g.add_edge("log_analyst", "timeline_builder")
    g.add_edge("timeline_builder", "change_reviewer")
    g.add_edge("change_reviewer", "planner")  # the loop: back to the planner for review
    g.add_edge("writer", END)
    return g
