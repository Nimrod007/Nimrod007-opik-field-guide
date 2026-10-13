# mastra-utility-account-agent

*A Mastra agent for a household electricity-and-water account, whose every tool call shows up in Opik as a real `execute_tool` span.*

![Node](https://img.shields.io/badge/node-22.13%2B-339933?logo=node.js&logoColor=white)
![Mastra](https://img.shields.io/badge/%40mastra%2Fcore-1.76.0-0b0b0b)
![Opik](https://img.shields.io/badge/Opik-OTel%20ingestion-2f54eb)

When an account assistant tells a customer "your water use spiked in August" or "a crew has been notified, ticket OUT-0001", you need to know where that came from: a tool result, or the model's imagination. A chat transcript cannot tell you. An agent trace tree can: each model step, and each tool the model chose to run with the exact arguments it chose, is its own span.

## What you'll build

A small support agent for Harborlight Utilities, a fictional utility. It runs on `gpt-4o-mini` through Mastra and has four tools over in-memory data:

- `get_meter_reading`: latest electricity or water meter reading for an account.
- `get_usage_history`: up to six months of kWh, m3 and bill totals, with water-spike months flagged.
- `check_known_outage`: whether the customer's service zone already has a published outage.
- `report_outage`: files a new ticket, and the instructions tell the agent to use it only after the check comes back empty.

The code is split the way a real service would be: `src/tools/`, `src/agents/`, `src/data/`, plus a CLI (`src/cli.ts`) that plays four scripted customer questions. Tracing is only in `src/mastra.ts`: Mastra's observability layer plus its `OtelExporter`, aimed at Opik's OpenTelemetry endpoint. Neither the agent nor the tools mention tracing.

## See it in Opik

Open the project `mastra-utility-account-agent` (workspace `default`). After one `npm run demo` it holds 4 traces, all named `invoke_agent harborlight-account-agent`, one per customer question. The Output column in the trace list is empty for all four (see Gotchas), so judge them by their trees.

Open the last trace (the water-pressure report). It has 21 spans: three `chat gpt-4o-mini` LLM spans (about 500 prompt tokens each, with prompt, completion and total token counts), three `agent_step` spans, and two `execute_tool` spans, `execute_tool checkOutageTool` followed by `execute_tool reportOutageTool`. Click the second one: its input holds `gen_ai.tool.call.arguments` with the account id and the `water` kind the model extracted from prose, and its output holds `gen_ai.tool.call.result` with `ticketId: OUT-0001` and `status: crew-notified`. The outage question for `HL-31977` is the contrast: only one tool span (`checkOutageTool`, `known: true`, zone `east-ridge`) and no ticket. The meter and usage questions each have a single `execute_tool` span (`meterReadingTool`, `usageHistoryTool`), the latter returning `waterSpikeMonths: ["2026-08"]`, which is where the agent's "August water spike" comes from.

Expect some extra `general` spans in each tree (`model_generation`, `model_chunk`, `processor_run`); they are Mastra's internals, and the useful signal is the `agent_step` > `chat` / `execute_tool` structure. Span types in Opik are `llm` for `chat`, `tool` for `execute_tool` and `general` for the rest.

## Run it yourself

Needs Node 22.13+, a local Opik at `http://localhost:5173`, and an OpenAI key in `.env` (here or in a parent folder).

1. `cd mastra-utility-account-agent && cp .env.example .env` and add `OPENAI_API_KEY`.
2. `npm install`
3. `OPIK_URL_OVERRIDE=http://localhost:5173/api/ OPIK_WORKSPACE=default npm run demo`
4. Open the project in Opik and click the newest trace.
5. Tests, offline, no keys, tracking off: `OPIK_TRACK_DISABLE=true npm test`

## Poke around

- Change the fourth question in `src/script.ts` to a customer in `east-ridge` (account `HL-31977`) and watch the agent stop after `check_known_outage`, with no ticket filed.
- Ask about an account that does not exist (`HL-00000`). The tool span returns the `error` object and you can read how the agent words it.
- Lower `maxSteps` to 1 in `src/cli.ts`: the trace shrinks to one `chat` span that never reaches a tool.
- Edit the `instructions` in `src/agents/account-agent.ts` to drop the "check before report" rule and see whether the agent files tickets during a known outage.

## Gotchas we hit

**The trace's Output column is empty.** Mastra's OTel mapping puts the agent's input on the root `invoke_agent` span (as `mastra.agent_run.input`) but never sets a trace-level output, so every trace in the list shows no output. The answer is still there: open a trace and read the last `chat` span, or the `execute_tool` spans' `gen_ai.tool.call.result`. Fixing it would need a custom span processor that copies the final text onto the root span; this example leaves it alone.

**Cost is blank even though token usage is there.** The `chat` spans carry `prompt_tokens` and `completion_tokens`, but `total_estimated_cost` stays null: the provider arrives as `openai.responses`, which Opik does not recognise as a priced provider. Treat the token counts as the signal here and compute dollars yourself if you need them.

**Traces land in "Default Project".** The OTLP endpoint picks the project from a `projectName` header. Put it in the exporter's `headers` (see `src/mastra.ts`); `serviceName` alone does not choose the project.

**Nothing is exported at exit.** Spans are batched. Call `await mastra.shutdown()` before the process ends (the CLI does) or the final trace may never leave.

## How it's put together

- `src/data/accounts.ts`: fictional accounts, meter readings, six months of usage, a published outage, and the list of filed tickets.
- `src/tools/meter.ts`, `usage.ts`, `outage.ts`: plain functions plus Mastra `createTool` wrappers; `index.ts` re-exports them.
- `src/agents/account-agent.ts`: the agent: model, instructions, tools.
- `src/mastra.ts`: the Mastra instance and the Opik `OtelExporter` (skipped when `OPIK_TRACK_DISABLE=true`).
- `src/script.ts`, `src/cli.ts`: the scripted questions and the runner that flushes at the end.
- `tests/tools.test.ts`, `tests/mastra.test.ts`: vitest checks of the tool logic and of the Mastra instance with tracking disabled.

---

*built with Opik · inspired by Opik's examples and documentation*
