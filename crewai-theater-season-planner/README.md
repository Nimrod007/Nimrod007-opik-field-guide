<div align="center">

# Theater Season Planner

**`crewai-theater-season-planner`**

*Three CrewAI agents plan a season for a community theater, and Opik shows what each one cost.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![CrewAI](https://img.shields.io/badge/crewai-1.15-FF5A50?style=flat)
[![Opik](https://img.shields.io/badge/Opik-2.2.99-2f54eb?style=flat)](https://github.com/comet-ml/opik)

</div>

---

A crew of agents hands you one finished answer. What you cannot see is which specialist produced which part, what each was given, and who spent the tokens. This example puts a three-agent CrewAI crew behind a single `track_crewai` call so that every `kickoff()` becomes one Opik trace, with token counts and a dollar figure on each model call, and then adds a small script that rolls those numbers up per agent.

## What you'll build

The Alderbank Players, a fictional volunteer theater, need a five-play season. Three agents run in sequence on `gpt-4o-mini`:

1. **Programming Dramaturg** picks five plays from `data/play_candidates.csv`.
2. **Budget Manager** adds up the production costs and compares them with the spendable budget derived from `data/budget.csv` (income, minus fixed costs, marketing and the untouchable reserve: $37,500).
3. **Rehearsal Scheduler** places the approved plays in the slots of `data/venue_calendar.csv`.

Everything comes from local files, so the run needs only an OpenAI key. `cost_report.py` then reads the trace back from Opik and prints tokens and cost per agent.

## See it in Opik

Open the `crewai-theater-season-planner` project. One run gives exactly one trace, named `kickoff`, with 49 spans and a total estimated cost of about $0.0007 (2,651 tokens).

Expand it. Under the root there is one `Task: ...` span per task (`Shortlist the plays`, `Check the budget`, `Schedule the season`), and under each one a span named after the agent (`Programming Dramaturg`, ...). Below an agent sit CrewAI's internal planning steps, and inside them the one `llm` span, `chat_completion_create`, that did the work. Only those `llm` spans carry the model (`gpt-4o-mini-2024-07-18`), prompt and completion tokens and cost; the `general` spans around them show none.

In the verified run the per-agent split was:

| agent | prompt tok | completion tok | cost USD |
|---|---|---|---|
| Rehearsal Scheduler | 913 | 278 | 0.000304 |
| Budget Manager | 708 | 209 | 0.000232 |
| Programming Dramaturg | 335 | 208 | 0.000175 |

Later agents cost more because each one receives the earlier tasks' output as context. Click the scheduler's `llm` span to see that input growing.

## Run it yourself

1. `cp .env.example .env` and set `OPENAI_API_KEY` (or rely on a repo-root `.env`). Opik settings come from `~/.opik.config` or the `OPIK_URL_OVERRIDE` / `OPIK_WORKSPACE` variables.
2. `uv sync`
3. `uv run main.py`
4. `uv run cost_report.py` to print the per-agent table for the newest trace.
5. Offline tests: `OPIK_TRACK_DISABLE=true uv run pytest`

## Poke around

- Change a royalty in `data/play_candidates.csv` and see which agent's span input changes and what the budget verdict becomes.
- Give only the scheduler `llm="gpt-4o"` and compare the rows in `cost_report.py`.
- Add a fourth agent (say, a marketing lead) and a task; add its role to `AGENT_ROLES` in `cost_report.py`.
- Run twice and compare the two traces' totals: how stable is the cost of one kickoff?

## Gotchas we hit

- **Cost is empty on agent and task spans.** Only `llm` spans have usage and cost; the trace and its ancestors sum them. To get per agent numbers, walk each `llm` span up to the span named after the agent role, as `cost_by_agent` does.
- **A successful run can still be a bad plan.** Exit code 0 and a tidy trace do not mean the crew obeyed the task: the first version asked for "five plays" but its final calendar listed six, two sharing a slot. Check the task spans' outputs, not just the cost.

## How it's put together

- `main.py` — the three agents, three tasks and the `track_crewai` call.
- `season_data.py` — loads the CSVs, computes production costs and the spendable budget, formats prompt text.
- `cost_report.py` — reads the latest trace from Opik and rolls usage and cost up per agent.
- `data/` — fictional plays, budget and venue calendar.
- `tests/` — offline tests for the data helpers, the roll-up logic, and a traced function with tracking disabled.

---

*built with Opik · inspired by Opik's examples and documentation*
