import main
from cost_report import cost_by_agent


def span(id, parent, name, type="general", usage=None, cost=None):
    return {"id": id, "parent_span_id": parent, "name": name, "type": type,
            "usage": usage, "total_estimated_cost": cost}


def test_cost_rolls_up_to_owning_agent():
    spans = [
        span("t1", None, "Task: Check the budget"),
        span("a1", "t1", "Budget Manager"),
        span("f1", "a1", "Flow.kickoff_async"),
        span("l1", "f1", "chat_completion_create", "llm",
             {"prompt_tokens": 700, "completion_tokens": 200}, 0.0002),
        span("l2", "f1", "chat_completion_create", "llm",
             {"prompt_tokens": 100, "completion_tokens": 50}, 0.0001),
    ]
    got = cost_by_agent(spans)["Budget Manager"]
    assert got["calls"] == 2 and got["prompt_tokens"] == 800
    assert abs(got["cost_usd"] - 0.0003) < 1e-12


def test_crew_is_wired_with_three_agents_and_tracking_disabled():
    assert [a.role for a in main.crew.agents] == [
        "Programming Dramaturg", "Budget Manager", "Rehearsal Scheduler"]
