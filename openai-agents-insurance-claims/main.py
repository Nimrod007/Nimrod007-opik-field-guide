"""Scripted claims-desk demo: three conversations, traced into Opik."""

import os
import uuid
from pathlib import Path

from dotenv import load_dotenv

# Load a repo-root .env if one exists, then pin the Opik project before opik
# is imported, so every trace lands in this project.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
os.environ.setdefault("OPIK_PROJECT_NAME", "openai-agents-insurance-claims")

import opik
from agents import Runner, set_trace_processors, trace
from opik.integrations.openai.agents import OpikTracingProcessor

from claims_desk import triage_agent

# Replaces the SDK's default exporter: agent runs, handoffs, tool calls and
# LLM generations all become spans in Opik. Without it nothing is logged.
set_trace_processors(processors=[OpikTracingProcessor()])

CONVERSATIONS = {
    # A storm drops a branch on a car: a house event, but the damage is auto.
    "branch-on-car": [
        "Policy HP-1001. A storm dropped a big branch on my parked car last night,"
        " about $3,200 of damage. What would I get paid?",
        "Please open the claim, the car is a 2019 hatchback.",
    ],
    # A lapsed policy: the specialist's lookup_policy span shows why it refuses.
    "lapsed-policy": [
        "Policy HP-1002. My kitchen caught fire, roughly $18,000 of damage."
        " Can you open a claim?",
    ],
    # Someone else was hurt on the policyholder's property: liability.
    "icy-steps": [
        "Policy HP-1003. A delivery driver slipped on my icy front steps and"
        " broke his wrist. File a claim.",
        "What's the status of claim CLM-7001?",
    ],
}


def run_demo() -> None:
    for name, turns in CONVERSATIONS.items():
        thread_id = f"{name}-{uuid.uuid4().hex[:6]}"
        print(f"\n=== {name} (thread {thread_id}) ===")
        history: list = []
        for message in turns:
            print(f"\nCustomer: {message}")
            history.append({"role": "user", "content": message})
            # One trace per turn. The shared group_id is what Opik shows as the
            # thread id, so the Threads tab stitches the turns back together.
            with trace(workflow_name="Claims triage", group_id=thread_id):
                result = Runner.run_sync(triage_agent, history)
            print(f"{result.last_agent.name}: {result.final_output}")
            history = result.to_input_list()


if __name__ == "__main__":
    try:
        run_demo()
    finally:
        # Spans are sent from a background queue; flush so a short script
        # doesn't exit before they are delivered.
        opik.flush_tracker()
