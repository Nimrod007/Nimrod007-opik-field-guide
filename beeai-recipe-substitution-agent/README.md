# beeai-recipe-substitution-agent

*Out of buttermilk mid-pancake? A BeeAI agent that rummages through your pantry, and a trace that shows exactly how it reasoned.*

![Node](https://img.shields.io/badge/node-20%2B-339933?style=flat&logo=node.js&logoColor=white)
![BeeAI](https://img.shields.io/badge/beeai--framework-0.1.13-f5c518?style=flat)
![Opik](https://img.shields.io/badge/Opik-OpenInference%20over%20OTLP-2f54eb?style=flat)

A ReAct agent writes its plan down as it goes: think, call a tool, think again. BeeAI's TypeScript framework gives you that loop in a few lines, then folds it into one `agent.run()` call. When the answer is wrong ("use 220 ml of oil"), you can't tell from the output whether the model misread the question, queried a tool badly, or ignored what came back. Here the agent helps home cooks in a fictional household kitchen, and every iteration, model call and tool call is exported to Opik as OpenTelemetry spans. There is no Opik SDK in the code.

## What you'll build

A BeeAI `ReActAgent` on `gpt-4o-mini` with three tools over JSON files in `data/`:

- `pantry_lookup` says what the household has in stock (`data/pantry.json`).
- `substitution_table` returns known swaps, each flagged `can_make_now` (`data/substitutions.json`).
- `unit_conversion` converts cups, tbsp, ml, grams and "each" using ingredient densities (`data/densities.json`).

`npm run demo` plays four scripted requests from `data/requests.json`: buttermilk for pancakes, two eggs in grams, 200 g of butter as millilitres of olive oil, and baking powder for biscuits. Tracing lives in one file, `src/tracing.ts`: BeeAI's OpenInference instrumentation, an OTel `NodeSDK`, and an OTLP exporter aimed at Opik.

## See it in Opik

Open the `beeai-recipe-substitution-agent` project and the Traces tab. One run gives 4 traces (one per request), each named `beeai-framework-main` and lasting 4 to 5 seconds, with about 2,700 to 4,100 tokens each. The trace Input and Output columns hold the full prompt and the agent's final answer.

Click a trace and expand it. Under the root span you will see `iteration-1` through `iteration-4`, one per ReAct turn. Inside them are `backend.openai.chat.*` spans of type **llm** with model `gpt-4o-mini` (token usage, around 1,100 to 1,600 prompt tokens, sits on the `success` span of each model call). Spans named `tool.dynamic.substitutionTable.*`, `tool.dynamic.pantryLookup.*` and `tool.dynamic.unitConversion.*` carry each tool's output as JSON. The trace for the butter request is the one to open. The agent first asked `substitution_table` for `"butter"`, which got back `No substitution known for "butter"` (the table is keyed `unsalted butter`). It then skipped the table, called `pantry_lookup` for olive oil, and `unit_conversion` turned 200 g into 219.78 ml, so the final answer said `220 ml of olive oil`. The table's real ratio (0.75 cup oil per cup butter) never got applied. That happened in both of the verified runs. The output alone looks plausible; the tool span with the error shows where it went wrong.

Cost: usage is recorded, but `total_estimated_cost` stays empty (see Gotchas).

## Run it yourself

1. `cd beeai-recipe-substitution-agent && npm install`
2. `cp .env.example .env`, then set `OPENAI_API_KEY` (a repo-root `.env` also works). For a local self-hosted Opik, set `OPIK_URL_OVERRIDE=http://localhost:5173/api` and `OPIK_WORKSPACE=default`. For Opik Cloud leave the URL unset and set `OPIK_API_KEY` and your workspace.
3. `npm run demo` (about 20 to 40 seconds, a few cents of `gpt-4o-mini`).
4. Open the project above in Opik.

Offline checks: `OTEL_SDK_DISABLED=true npm test` (no keys, no network; `OTEL_SDK_DISABLED=true` is OpenTelemetry's standard off switch, which `startTracing` honours) and `npm run typecheck`.

## Poke around

- Edit `data/substitutions.json` and rename `unsalted butter` to `butter`. Rerun and compare the butter trace: the table call now succeeds and the ratio shows up in the answer.
- Add an item to `data/requests.json`, such as a cook who needs cake flour. Watch which tool the agent reaches for first.
- Lower `maxIterations` in `src/agent.ts` to 2 and see what a cut-off loop looks like in the span tree.
- Zero out `milk` in `data/pantry.json` and rerun the buttermilk request. The `can_make_now` flags and the agent's `pantry_lookup` calls should disagree with the earlier run.

## Gotchas we hit

- **No spans appear at all, or only the root.** Under `tsx` the `beeai-framework` module is loaded before the instrumentation's import hook can patch it. Call `instrumentation.manuallyInstrument(beeaiFramework)` after `sdk.start()`, with `import * as beeaiFramework from "beeai-framework"`, and start tracing before importing the agent module (see `src/tracing.ts` and the dynamic imports in `src/demo.ts`).
- **The last request's spans are missing.** The OTLP exporter batches. Call `await sdk.shutdown()` before the process exits (`tracing.shutdown()` in `demo.ts`).
- **`total_estimated_cost` is empty although tokens are counted.** The OpenInference spans carry the model name and token counts but no provider attribute Opik can price from, and usage lands on the `success` spans only. I tried adding `llm.provider` / `gen_ai.system` and model attributes through a span processor and cost stayed null, so I removed it; treat usage as the signal here, or log cost yourself.
- **The agent spans are noisy.** BeeAI emits an event span for each emitter event (`agent.react.update-N`, `partialUpdate-N`), so one run has about 230 spans. Filter by names starting with `iteration-`, `backend.` and `tool.` to read the loop. Only the model calls get type `llm`; the rest are `general`.

## How it's put together

- `src/tracing.ts`: NodeSDK, BeeAI OpenInference instrumentation and the OTLP exporter pointed at Opik; `OTEL_SDK_DISABLED=true` turns it off.
- `src/kitchen.ts`: pure pantry lookup, substitution table and unit conversion logic.
- `src/tools.ts`: the three BeeAI `DynamicTool` wrappers.
- `src/agent.ts`: instructions and the `ReActAgent`.
- `src/demo.ts`: loads env, starts tracing, plays `data/requests.json`, flushes.
- `data/`: fictional pantry, substitutions, densities and the scripted requests.
- `tests/kitchen.test.ts`: vitest checks for the kitchen logic and for running the tools with tracing disabled.

---

*built with Opik · inspired by Opik's examples and documentation*
