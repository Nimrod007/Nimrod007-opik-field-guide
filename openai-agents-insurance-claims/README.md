# openai-agents-insurance-claims

*A claims line where one triage agent hands each customer to the right specialist, and Opik shows you every handoff and every tool call.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![OpenAI Agents SDK](https://img.shields.io/badge/openai--agents-0.23-412991?style=flat)
![Opik](https://img.shields.io/badge/Opik-2.2.99-2f54eb?style=flat)

When a claims assistant gives a bad answer, the customer sees one reply. You need to know *who* produced it: did triage send a storm-damaged car to the property team, did the specialist quote coverage without looking up the policy, or did a tool return something the model glossed over? This example is a small home-insurance claims desk on the OpenAI Agents SDK, traced with Opik's `OpikTracingProcessor`, so each customer turn becomes a tree you can read.

## What you'll build

Four `gpt-4o-mini` agents. A **Claims Triage Agent** never answers; it only hands off. Behind it sit an **Auto**, a **Property** and a **Liability Claims Agent**, each with function tools over fictional data in `claims_data.py` (three policies, two existing claims): `lookup_policy`, `estimate_payout` (damage minus deductible, capped at the category limit), `open_claim` and `claim_status`. Opik is wired with one call, `set_trace_processors([OpikTracingProcessor()])`. The demo plays three scripted conversations (five turns), each turn inside `trace(..., group_id=...)` so Opik can group turns into threads:

- `branch-on-car`: a storm drops a branch on a parked car. A house event, but the damage is a vehicle, so triage should pick Auto. Turn two opens the claim.
- `lapsed-policy`: a kitchen fire on a lapsed policy. The Property agent should look the policy up and refuse.
- `icy-steps`: a delivery driver slips on the policyholder's steps (Liability), then asks about an older claim.

## See it in Opik

Open the `openai-agents-insurance-claims` project and the **Traces** tab: five traces named `Claims triage`. Open the first `branch-on-car` trace and expand it. A `Task` span contains the `Claims Triage Agent` span (one LLM `Response`), then a `Handoff` span, then the `Auto Claims Agent` span. Inside that agent you will see `lookup_policy` and `estimate_payout` as **tool** spans. Click `estimate_payout` to see the arguments the model chose (`HP-1001`, `auto`, `3200`) and the JSON it got back (`estimated_payout_usd: 2700`). The final answer repeats that number. Per run in my check: 17 LLM spans, 7 tool spans, 37 general spans (task, agent, turn and handoff), every LLM span with token usage and cost, about $0.0015 in total.

Open the `lapsed-policy` trace and click its `lookup_policy` span: the output says `"status": "lapsed"`, which is why the Property agent declines and no `open_claim` span exists. That absent span is the evidence.

Switch to the **Threads** tab: three threads, `branch-on-car-<id>` (2 traces), `lapsed-policy-<id>` (1) and `icy-steps-<id>` (2). Each thread id is the `group_id` passed to `trace()`. Open `branch-on-car` and the payout question and the "please open the claim" follow-up read as one conversation.

## Run it yourself

1. `cp .env.example .env` and set `OPENAI_API_KEY` (or keep it in a parent `.env`, which is loaded too).
2. Make sure Opik is reachable. Local Opik is read from `~/.opik.config`; for Opik Cloud add `OPIK_API_KEY` and `OPIK_WORKSPACE`.
3. `uv sync`
4. `uv run main.py` (about 20 seconds, under a cent in tokens)
5. Open the `openai-agents-insurance-claims` project in Opik.

Tests need no keys and no Opik: `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`

## Poke around

- Rewrite the `branch-on-car` message to "A tree fell on my garage" and see whether triage chooses Property or Auto at the `Handoff` span.
- Delete `lookup_policy` from the Auto agent's tools and watch whether it still quotes coverage. The trace will show it did so with no policy data.
- Add a fourth specialist (say, a travel-delay agent) to `triage_agent.handoffs`. No tracing change is needed for it to appear.
- Remove `group_id` from `trace(...)` and refresh the Threads tab: the conversations fall apart into unrelated traces.

## Gotchas we hit

- **A specialist opened a claim nobody asked for.** In my first run the Auto agent answered "what would I get paid?" and also called `open_claim`; the trace showed the tool span in turn one. Cause: the instructions said "open_claim when the customer asks to file", and the model read a payout question as intent. Fix: say it as a rule in the prompt (`Only call open_claim if the customer explicitly asks you to file or open one.`) and keep payout and filing tools described separately.
- **Triage answered a claim-status question itself.** The trace for that turn had no `Handoff` and no specialist span, only the triage LLM call saying it can't check claims. Cause: the triage prompt covered new claims but not status lookups. Fix: add `Status questions about an existing claim also go to a specialist`. Missing handoffs are easy to spot in Opik precisely because the `Handoff` span is absent.
- **Re-running piles traces into the same project.** Each run adds five traces; threads will look duplicated. Delete old traces first (for example `POST /api/v1/private/traces/delete` with `{"ids": [...]}`), or set `OPIK_PROJECT_NAME` to a new project.

## How it's put together

- `main.py`: sets the Opik project, installs `OpikTracingProcessor`, runs the three conversations with `group_id` threads, flushes.
- `claims_desk.py`: the four agents, handoff wiring and `@function_tool` wrappers.
- `claims_data.py`: fictional policies and claims plus the pure payout and claim-opening rules.
- `tests/test_claims.py`: payout math, lapsed-policy refusals, claim id assignment.
- `tests/test_agents.py`: handoff wiring, tool lists, and the tracing processor plus `trace()` block running with tracking disabled.

---

*built with Opik · inspired by Opik's examples and documentation*
