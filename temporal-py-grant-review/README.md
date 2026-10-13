# temporal-py-grant-review

*A community-grant review that runs on Temporal across two processes, and still shows up in Opik as one trace, retry and all.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![Temporal](https://img.shields.io/badge/temporalio-1.34-000000?style=flat)
![Opik](https://img.shields.io/badge/opik-2.2.99-2f54eb?style=flat)

When a workflow engine runs your agent, the code that starts the work and the code that does it live in different OS processes. Each process has its own tracing context, so by default you get two disconnected fragments, and when Temporal quietly retries a flaky step, the failed attempt is easy to miss. This example is a grant-review pipeline for a fictional "Harbor County Community Fund". It keeps one Opik trace across the client and the worker, with the failed attempt and its retry both visible.

## What you'll build

A `GrantReviewWorkflow` that processes one application through four activities:

1. `check_eligibility`: plain rules (service area, organization type, funding cap).
2. `score_rubric`: `gpt-4o-mini` scores the pitch on four criteria, 1 to 5.
3. `check_budget`: line items must add up and soft costs must stay under 20%. It reads a "finance ledger" that **fails with a 503 on the first attempt**, so Temporal retries it (1 s backoff, up to 4 attempts).
4. `write_letter`: the model drafts the decision letter (approve, revise or decline).

Trace propagation is deliberately simple. The client opens a tracked span, calls `opik_context.get_distributed_trace_headers()`, and passes the two ids as ordinary data inside the workflow input. The workflow copies them onto each activity input, and each activity calls a `@opik.track` function with `opik_distributed_trace_headers=...`, which attaches its span to the client's trace. No Temporal interceptors are needed.

## See it in Opik

Open the **temporal-py-grant-review** project and the Traces tab. A run produces two traces, both named `grant-review` (one per application, 8 spans each). Open one and expand the tree:

- `grant-review` (general) is the client span, and its metadata has the client process pid.
- Beneath it are `activity:check_eligibility` (tool), `activity:score_rubric` (general, with a `chat_completion_create` llm child), then **two** `activity:check_budget` (tool) spans, and finally `activity:write_letter` (general, with its own llm child).
- All the activity spans carry a different `pid` in their metadata (the worker's) than the root span, which shows they came from another process.
- The first `check_budget` span is marked as an error: `ConnectionError: Finance ledger unavailable (503) ...`, with `temporal_attempt: 1`. The second, a second later, is clean with `temporal_attempt: 2`.
- The two llm spans show token usage and cost, roughly $0.00004 for the scoring call and $0.0001 for the letter. A whole run costs under a tenth of a cent.

Temporal's own UI at http://localhost:8233 shows the workflow history. Opik adds what the model said and what it cost, tied to the attempt that produced it.

## Run it yourself

1. Install [uv](https://docs.astral.sh/uv/) and the [Temporal CLI](https://docs.temporal.io/cli), then start a local dev server in another terminal: `temporal server start-dev` (listens on `localhost:7233`, no Docker).
2. Point Opik somewhere: `opik configure`, or set `OPIK_API_KEY` and `OPIK_WORKSPACE` for Opik Cloud. (A local self-hosted Opik is picked up from `~/.opik.config`.)
3. `cp .env.example .env` and set `OPENAI_API_KEY`.
4. `uv sync`
5. `uv run python demo.py`. It spawns `worker.py` as a separate process, reviews both applications in `data/applications.json`, prints the decisions and letters, then stops the worker. It takes about 20 seconds.
6. Open the project in Opik and click the newest trace.

Tests need no keys, no Temporal and no Opik: `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`.

## Poke around

- In `activities.py`, change `attempt == 1` to `attempt <= 3` and re-run: the trace grows to three red `check_budget` spans and one green.
- Delete the `opik_distributed_trace_headers=...` argument from one activity. That activity's spans land in their own separate traces, so the trace tree breaks right where the headers stop.
- Set `county` of an application to something other than "Harbor County" in `data/applications.json`: the workflow skips scoring and budget entirely and writes a decline letter, so the trace is shorter.
- Raise `FLAKY.initial_interval` in `workflows.py` and read the gap between the two `check_budget` spans on the timeline.

## Gotchas we hit


- **Symptom:** client and worker spans appear in different projects. **Cause:** Opik's project is chosen per process. **Fix:** `config.py` is imported by both entry points and sets `OPIK_PROJECT_NAME` to the same value.
- **Symptom:** retries show up as one span. **Cause:** a retry reruns the whole activity function. **Fix:** put `@opik.track` on a helper the activity calls, so every attempt opens its own span, and write `activity.info().attempt` to the span metadata (`_tag_attempt`).

## How it's put together

- `demo.py`: client process; opens the root span, starts the workflow, spawns and stops the worker.
- `worker.py`: worker process; registers the workflow and activities, flushes Opik on exit.
- `workflows.py`: the durable workflow and its retry policy.
- `activities.py`: the four activities and their tracked helpers, `track_openai` client, deliberate transient failure.
- `grants.py`: pure rules, rubric parsing, budget check, decision logic, and the input dataclasses.
- `config.py`: shared env loading, project name and task queue.
- `data/applications.json`: two fictional applications.
- `tests/test_grants.py`, `tests/test_activities.py`: offline tests of the logic and of traced activities with tracking disabled and a stubbed model.

The worker also logs the first-attempt `ConnectionError` traceback to the terminal; that is the deliberate failure, not a bug.

---

*built with Opik · inspired by Opik's examples and documentation*
