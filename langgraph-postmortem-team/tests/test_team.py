"""Offline tests: no provider key, no Opik. Run with OPIK_TRACK_DISABLE=true."""

from types import SimpleNamespace

from postmortem import team
from postmortem.corpus import load_sections, rank, search_evidence


def test_every_data_file_splits_into_sections():
    for name in ("logs.md", "chat.md", "deploys.md"):
        sections = load_sections(name)
        assert len(sections) >= 6
        assert all(s["heading"] and s["source"] == name for s in sections)


def test_rank_finds_the_blocked_rollback():
    top = rank("why was the rollback blocked by the canary gate", load_sections("logs.md"), k=1)
    assert "14:24" in top[0]["heading"]


def test_traced_search_works_with_tracking_disabled():
    # search_evidence is decorated with @opik.track; with tracking off it behaves as a plain function.
    hits = search_evidence("retry mobile app backoff", ["deploys.md"], k=2)
    assert hits[0]["source"] == "deploys.md" and "8.4.0" in hits[0]["text"]


def test_routing_follows_the_planner_verdict():
    assert team.route_after_planner({"ready": True}) == "writer"
    assert team.route_after_planner({"ready": False}) == "log_analyst"


class FakeLLM:
    def invoke(self, messages):
        return SimpleNamespace(content="stub answer")


def test_investigator_skips_without_assignment_and_records_finding(monkeypatch):
    monkeypatch.setattr(team, "get_llm", lambda: FakeLLM())
    node = team.make_investigator("change_reviewer")
    assert node({"assignments": {"log_analyst": "x"}, "round": 1}) == {}
    out = node({"assignments": {"change_reviewer": "what changed before 14:00"}, "round": 2})
    finding = out["findings"][0]
    assert finding["agent"] == "change_reviewer" and finding["round"] == 2
    assert finding["answer"] == "stub answer" and "deploys.md" in finding["sources"]


def test_graph_has_the_loop_edge():
    graph = team.build_graph().compile().get_graph()
    edges = {(e.source, e.target) for e in graph.edges}
    assert ("change_reviewer", "planner") in edges and ("planner", "writer") in edges
