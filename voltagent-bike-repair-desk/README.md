# voltagent-bike-repair-desk

*A VoltAgent repair-intake assistant for a bike shop, where every LLM span in Opik carries token usage and a real dollar cost.*

![Node](https://img.shields.io/badge/node-20.19%2B-339933?style=flat&logo=node.js&logoColor=white)
![VoltAgent](https://img.shields.io/badge/%40voltagent%2Fcore-2.x-1b1f23?style=flat)
![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-OTLP-425cc7?style=flat)

OpenTelemetry gets an agent's spans into Opik in a few lines. Getting them in *usefully* is the harder part. VoltAgent names its attributes `llm.usage.prompt_tokens` and `llm.model`, while Opik reads the `gen_ai.*` family. If you skip the translation, the traces still arrive, but the LLM spans are untyped, carry no token counts, and have no cost, so you cannot answer "what did this conversation cost?". This example is a small, runnable fix for that, built around a bike-shop front desk.

## What you'll build

The assistant works the intake desk at Spoke & Sprocket Cycle Works, a fictional shop. It runs on `gpt-4o-mini` and has three tools over in-memory data: `lookup_parts` (price and stock per SKU), `quote_repair` (flat labor plus parts) and `book_slot` (takes a bench slot off the board). `npm run demo` plays three scripted customers:

1. Squealing brakes: asks for pad price, stock and a brake-service quote.
2. A worn 11-speed drivetrain: wants a chain-and-cassette quote (the cassette is out of stock).
3. A plain booking: a gear tune-up for Priya Nair on 2026-11-02 at 13:00.

Tracing lives in one file, `src/observability.ts`. It registers an OTLP exporter pointed at Opik's OTel endpoint and wraps it in a small exporter that, just before export, copies VoltAgent's attributes to their `gen_ai.*` names and adds the provider. No agent or tool file mentions tracing.

## See it in Opik

Open the project `voltagent-bike-repair-desk`. The Traces tab shows 3 traces, one per customer, and each has 3 to 6 spans (13 in total). Open any trace and you will see:

- An `llm:generateText` span typed **llm**, with model `gpt-4o-mini`, provider `openai`, token usage and an estimated cost. In one run the first customer's span showed 444 prompt + 53 completion = 497 tokens and a cost of about $0.0001, and the three llm spans together cost roughly $0.0003. That non-null cost on the llm span is the point of the example.
- `tool.execution:lookup_parts`, `tool.execution:quote_repair` and `tool.execution:book_slot` spans typed **tool**. Customer 2 is the interesting one: the model calls `lookup_parts` several times, then `quote_repair`, and the `lookup_parts` output shows `CAS-118` with `stock: 0`, which is why the reply warns that the cassette is unavailable.
- A root `repair-intake-assistant` span (type general) holding the whole turn and the final reply.

Now try the baseline. Run `OPIK_SKIP_MAPPING=true npm run demo` (delete the earlier traces first so the counts stay readable). The traces arrive, but every span is `general`, the llm spans have no usage and no cost, and the tool spans lose their typing. When we checked, the only difference between the two runs was the mapping wrapper.

Trace-level input/output in Opik shows VoltAgent's raw attribute payload with the text under an `output` key, since this is a plain OTel mapping and not a native integration.

## Run it yourself

1. Have a local Opik running at `http://localhost:5173` (workspace `default`), or point `OPIK_OTEL_ENDPOINT` and `OPIK_API_KEY` at Opik Cloud.
2. `cp .env.example .env` and set `OPENAI_API_KEY` (or rely on a repo-root `.env`).
3. `npm install`
4. `npm run demo` (takes about a minute; a full run costs well under a cent).
5. Open the `voltagent-bike-repair-desk` project in Opik and click the newest trace.
6. `npm test` runs the offline tests (see below).

## Poke around

- Run with `OPIK_SKIP_MAPPING=true` and compare the llm span before and after.
- In `mapToGenAI`, change `provider` to a made-up string and see what happens to the cost column.
- Add a fourth customer who asks for `2026-11-04` (no open slots) and read what `book_slot` returned in its span, and how the agent explained it.
- Swap `MODEL` in `src/agent.ts` for another OpenAI model and check that the cost per token changes accordingly.

## Gotchas we hit

**Symptom: the traces arrive but the llm spans show no token usage, no cost, and every span type is `general`.**
Cause: VoltAgent emits `llm.usage.*` and `llm.model` (and `span.type` is its own attribute), while Opik looks for `gen_ai.*` attributes. The exporter does not translate them.
Fix: wrap the OTLP exporter and add the `gen_ai.*` copies before export, as `mapToGenAI` does:

```ts
attrs["gen_ai.request.model"] = attrs["llm.model"];
attrs["gen_ai.provider.name"] = "openai";           // the provider is what lets Opik price the tokens
attrs["gen_ai.usage.prompt_tokens"] = attrs["llm.usage.prompt_tokens"];
```

**Symptom: the AI SDK prints "System messages in the prompt" on every call.**
Cause: VoltAgent puts the system prompt in the messages array and does not expose the SDK option that acknowledges it.
Fix: the CLI filters that one known warning from `console.warn`.

## How it's put together

- `src/shop.ts`: fictional parts, labor rates and bench slots, plus the three tools and their plain implementations.
- `src/agent.ts`: the `gpt-4o-mini` intake assistant and its instructions.
- `src/observability.ts`: OTLP exporter to Opik and the `gen_ai.*` mapping wrapper (the only tracing code).
- `src/cli.ts`: loads env, plays the three scripted customers, shuts the exporter down to flush.
- `tests/shop.test.ts`: offline vitest tests for the tools, the attribute mapper, and a tool call with export disabled.
- `.env.example`: every setting the example reads.

Tests run with no keys and export off (`OTEL_SDK_DISABLED=true` leaves VoltAgent with no span processor):
`env -u OPENAI_API_KEY OTEL_SDK_DISABLED=true npm test`.

---

*built with Opik · inspired by Opik's examples and documentation*
