# langgraph-postmortem-team

*A planner, three investigators and a writer reconstruct an outage, and Opik shows you the loop they went around to do it.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/langgraph-1.x-1C3C3C?style=flat)
[![Opik](https://img.shields.io/badge/Opik-2.2.99%2B-2f54eb?style=flat)](https://github.com/comet-ml/opik)

A post-mortem is a good job for a team of agents and a hard one to debug. The evidence is scattered (logs, chat, deploy history), the first pass is never complete, and when the final document gets a detail wrong you want to know which agent dropped it and in which round. A flat list of LLM calls can't tell you that. This example builds the team in LangGraph and traces it with Opik so the whole investigation is one trace you can walk through, with the planner's loop drawn in the agent graph and a dollar figure on every agent.

## What you'll build

A graph of five nodes about a fictional outage: the Marlin checkout service returned HTTP 503s for 47 minutes on 2026-03-14.

```
planner -> log_analyst -> timeline_builder -> change_reviewer -> planner (review) -> ... -> writer
              ^_______________ loop while the planner is not satisfied ____________|
```

- **planner** assigns each investigator an opening question, then, after every round, reviews the findings. It is only satisfied when the root cause is backed by two kinds of evidence and the slow recovery is explained. Otherwise it sends targeted follow-ups (at most three rounds).
- **log_analyst, timeline_builder, change_reviewer** each search their own slice of `data/` (service logs, an incident chat channel, deploy and config history) with a small keyword ranker, then answer from those excerpts. An investigator with no follow-up this round skips without calling the model.
- **writer** turns every finding into a blameless post-mortem.

Everything runs on `gpt-4o-mini`. The corpus is three short markdown files, no web, no vector database.

## See it in Opik

Open the **langgraph-postmortem-team** project. One run produces one trace named `LangGraph`, about 43 seconds long, with 45 spans and roughly 18,000 tokens for about $0.004 in total.

- **Agent graph.** Open the trace and switch to the graph view. The five nodes are drawn with the edge from `change_reviewer` back to `planner`, so the loop is visible as a loop, not inferred from repeated names.
- **The tree.** Expand it and you see the passes in order: `planner` (4 passes: the plan plus three reviews), then `log_analyst`, `timeline_builder`, `change_reviewer` once per round, and finally `writer`. In my run the second round only woke two investigators, and the third a different two; the third pass of the idle one is an empty span with no LLM call under it. The planner's output on each pass says why it asked for another round.
- **Tool spans.** Each active investigator has a `search_evidence` tool span with the query and the six excerpts it was handed, followed by its `ChatOpenAI` llm span. When a finding is wrong you can tell at a glance whether the right section was retrieved.
- **Cost per agent.** Every one of the 12 llm spans carries provider `openai`, model `gpt-4o-mini-2024-07-18`, token usage and an estimated cost. Summing llm spans under each node in my run: planner $0.0012 (four calls), timeline_builder $0.0012, change_reviewer $0.0006, log_analyst $0.0004, writer $0.0009. The planner's loop is the cost lever: each extra review round buys another planner call plus the investigations it triggers.

Your numbers will differ a little, since the planner decides how many follow-ups to request.

## Run it yourself

1. `cd langgraph-postmortem-team`
2. `cp .env.example .env` and set `OPENAI_API_KEY` (a repo-level `.env` one directory up also works). Point Opik at your instance with `opik configure`, or leave it on the default.
3. `uv sync`
4. `uv run main.py` and watch the rounds and the finished post-mortem print.
5. Open the `langgraph-postmortem-team` project in Opik and click the newest trace.

Offline tests (no key, no Opik): `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`

## Poke around

- Change `MAX_ROUNDS` in `postmortem/team.py` to `1` and compare traces: there is only one investigation pass, so the follow-up evidence that explains the rollback delay.
- Delete the "rollback gate policy" section from `data/deploys.md`. Watch whether the planner still asks about the rollback, and whether the writer admits what it can't source.
- Drop the "per pod" detail from `cfg-2291` in `data/deploys.md` and see which agent first loses the misreading of the config.
- Swap the planner's "ready_to_write" rule for a single-source rule and check how many rounds and dollars it saves.

## Gotchas we hit

- **`openai.OpenAIError: Missing credentials` when running `pytest`.** Building `ChatOpenAI(...)` at module import needs a key, so tests fail at collection even though they stub the model. Create the client lazily (`functools.cache` around a `get_llm()` function) and monkeypatch that in tests.
- **`result["round"]` is one higher than the rounds you saw.** The final planner pass is forced to `ready_to_write` when the round budget is spent, so `result["round"]` ends one higher than the number of investigation rounds. The code prints `round - 1`.

## How it's put together

- `main.py` - sets the Opik project, builds the traced graph with `OpikTracer` and `track_langgraph`, runs it once and flushes.
- `postmortem/team.py` - state, the planner (plan and review), the investigators, the writer and the graph wiring with the loop edge.
- `postmortem/corpus.py` - section loader, rarity-weighted ranker and the `search_evidence` tool span.
- `data/` - logs, chat excerpts and deploy history for the fictional outage.
- `tests/test_team.py` - offline tests for the ranker, routing, investigator logic, the loop edge and a traced function with tracking disabled.

---

*built with Opik · inspired by Opik's examples and documentation*
