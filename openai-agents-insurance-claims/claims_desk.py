"""Agents and tools for the claims desk: one triage agent, three specialists."""

import json

from agents import Agent, function_tool

import claims_data as data

MODEL = "gpt-4o-mini"


# Each @function_tool call becomes a tool span in Opik, with the arguments the
# model chose as input and the JSON string below as output.
@function_tool
def lookup_policy(policy_id: str) -> str:
    """Look up a policy: status, deductible, per-category limits, exclusions."""
    return json.dumps(data.lookup_policy(policy_id))


@function_tool
def claim_status(claim_id: str) -> str:
    """Get the status, summary and adjuster for an existing claim."""
    return json.dumps(data.claim_status(claim_id))


@function_tool
def estimate_payout(policy_id: str, category: str, damage_usd: float) -> str:
    """Estimate a payout. category must be one of: auto, property, liability."""
    return json.dumps(data.estimate_payout(policy_id, category, damage_usd))


@function_tool
def open_claim(policy_id: str, category: str, summary: str) -> str:
    """Open a new claim. category must be one of: auto, property, liability."""
    return json.dumps(data.open_claim(policy_id, category, summary))


COMMON = (
    " Always call lookup_policy first and never invent coverage details. If the"
    " policy is not active, say so and do not open a claim. Only call open_claim"
    " if the customer explicitly asks you to file or open one. Keep replies under"
    " four sentences."
)

auto_agent = Agent(
    name="Auto Claims Agent",
    handoff_description="Vehicle damage: collisions, hail on cars, theft from a car.",
    instructions="You handle auto claims." + COMMON +
    " Use estimate_payout (category auto) to answer payout questions.",
    model=MODEL,
    tools=[lookup_policy, estimate_payout, open_claim, claim_status],
)

property_agent = Agent(
    name="Property Claims Agent",
    handoff_description="Damage to the house itself or belongings: fire, water, storm, theft.",
    instructions="You handle property claims." + COMMON +
    " Use estimate_payout (category property) to answer payout questions.",
    model=MODEL,
    tools=[lookup_policy, estimate_payout, open_claim, claim_status],
)

liability_agent = Agent(
    name="Liability Claims Agent",
    handoff_description="Injury or damage the policyholder caused to someone else.",
    instructions="You handle liability claims." + COMMON +
    " File with open_claim (category liability) when asked.",
    model=MODEL,
    tools=[lookup_policy, open_claim, claim_status],
)

triage_agent = Agent(
    name="Claims Triage Agent",
    instructions=(
        "You are the front desk of a home-insurance claims line. Never answer"
        " the claim yourself: hand off to the auto, property or liability"
        " specialist. If damage is to a car, choose auto even when a house"
        " event caused it; if someone else was hurt or their things damaged,"
        " choose liability. Status questions about an existing claim also go to a"
        " specialist: pick the one matching the claim's category, or property if unsure."
    ),
    model=MODEL,
    handoffs=[auto_agent, property_agent, liability_agent],
)
