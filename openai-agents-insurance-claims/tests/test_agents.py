"""Wiring tests that run with tracking disabled and without any API key."""

from agents import set_trace_processors, trace
from opik.integrations.openai.agents import OpikTracingProcessor

from claims_desk import auto_agent, liability_agent, property_agent, triage_agent


def test_triage_hands_off_to_three_specialists():
    names = {h.name for h in triage_agent.handoffs}
    assert names == {a.name for a in (auto_agent, property_agent, liability_agent)}


def test_liability_agent_has_no_payout_tool():
    assert "estimate_payout" not in {t.name for t in liability_agent.tools}
    assert "estimate_payout" in {t.name for t in auto_agent.tools}


def test_tracing_processor_and_trace_block_are_harmless_when_tracking_disabled():
    # With OPIK_TRACK_DISABLE=true the processor is a no-op, so the same
    # setup used by main.py works inside unit tests.
    set_trace_processors(processors=[OpikTracingProcessor()])
    with trace(workflow_name="Claims triage", group_id="unit-test"):
        pass


def test_tools_are_exposed_with_their_function_names():
    assert {t.name for t in property_agent.tools} == {
        "lookup_policy", "estimate_payout", "open_claim", "claim_status"}
