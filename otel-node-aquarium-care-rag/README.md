# otel-node-aquarium-care-rag

*A Node microservice that never imports an Opik SDK, yet every answer it gives shows up in Opik as a trace.*

![Node](https://img.shields.io/badge/node-%E2%89%A520-5FA04E?style=flat&logo=nodedotjs&logoColor=white)
![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-OTLP-425CC7?style=flat&logo=opentelemetry&logoColor=white)
![Hono](https://img.shields.io/badge/hono-4-E36002?style=flat)
[![Opik](https://img.shields.io/badge/Opik-OTLP%20ingest-2f54eb?style=flat)](https://github.com/comet-ml/opik)

Plenty of production services are already instrumented with OpenTelemetry, or can be in an afternoon, and
not all of them are Python or have a first-party Opik client. Opik accepts OTLP directly, so any service that can
emit spans can ship them. The catch is in the details: the span attributes you choose decide
whether Opik sees a model name, token counts, a cost, and, the part that is easy to miss, the actual prompt and answer.
This example is a small fish-care FAQ service built to get those details right and to show what happens when you don't.

## What you'll build

A Hono HTTP service for a fictional shop, Brindle Reef Aquatics. At startup it splits four short care guides in
`docs/` (water parameters, tank mates, feeding, disease signs) into section chunks and embeds them with
`text-embedding-3-small`. `POST /ask {"question": "..."}` embeds the question, takes the top 3 chunks by cosine
similarity, and asks `gpt-4o-mini` to answer from those excerpts only, or say it does not know.

Tracing is plain OpenTelemetry JS: a `NodeTracerProvider`, a batch processor, and the OTLP/HTTP-protobuf
exporter pointed at Opik. The spans are written by hand in `src/rag.ts` and `src/server.ts` using the GenAI
semantic-convention attribute names (`gen_ai.request.model`, `gen_ai.usage.input_tokens`, ...). `src/demo.ts` boots the
service, sends five scripted questions over real HTTP, shuts the server down and flushes the exporter.

## See it in Opik

Open the project **otel-node-aquarium-care-rag** after a run. It holds 6 traces: five named `POST /ask`, one per
question, and one `ingest_care_guide` from startup.

Open any `POST /ask` trace. It has 4 spans nested under the request span: `retrieve_care_guide` (input is the
question and `top_k`, output is the three chunks picked, with source file, heading and similarity score), an
`embeddings text-embedding-3-small` llm span inside it, and `chat gpt-4o-mini`, an llm span. On the chat span
the Input panel shows the system prompt plus the excerpts plus the question, the Output panel shows the answer,
and the usage and cost columns are filled: the heater question used 308 prompt and 12 completion tokens for
an estimated $0.000053, and the five questions cost between $0.000051 and $0.000064 each. The trace list's
Input column shows the question (next to the HTTP method and path) and Output shows the answer with its sources. The heater question (which the guide never covers) comes back as "I don't
know", and the `retrieve_care_guide` output shows why: its best chunk scored only 0.384.

Two honest limits: Opik types the span from the `gen_ai.*` attributes, so the chat and embeddings spans are `llm`
but the retrieval and request spans show as `general` (I found no OTLP attribute that makes Opik label one a `tool`).
And the dollar cost is computed by Opik from the token counts and a model price table, which only works
because the span says which provider it is (see Gotchas).

## Run it yourself

1. Install: `npm install`
2. Keys: `cp .env.example .env` and put your `OPENAI_API_KEY` in it (a `.env` one directory up works too).
   Opik is expected at `http://localhost:5173`; for Opik Cloud set `OTEL_EXPORTER_OTLP_ENDPOINT` and `OPIK_API_KEY`.
3. Run the scripted demo: `npm run demo`. It boots the server on port 4290, asks five questions, closes the
   server and flushes spans (about 6 seconds, well under a cent).
4. Read the project back: `npm run check`. It queries Opik's REST API and fails if a question trace lacks usage, cost or text.
5. To run the service on its own: `npm run dev`, then
   `curl -s localhost:4290/ask -H 'content-type: application/json' -d '{"question":"How often do I change water?"}'`.
6. Tests (no keys, no Opik, tracing off): `OTEL_SDK_DISABLED=true npm test`.

## Poke around

- Unset `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` (or set it to `false`) and rerun the demo. Usage and cost still arrive; the chat span's Input and Output go blank.
- Delete the `gen_ai.provider.name` and `gen_ai.system` lines in `genAiBase()` in `src/rag.ts` and watch the cost column go to null while the token counts stay.
- Change `TOP_K` in `src/config.ts` to 1 and ask the tank-mates question; compare what `retrieve_care_guide` returns.
- Ask something the docs half-cover (for example "Can I keep a goldfish with tetras?") and read the retrieval scores to judge whether the answer was grounded.

## Gotchas we hit

**The chat span in Opik has no input or output, only usage.** GenAI semantic conventions treat prompts and
completions as potentially sensitive, so content capture is opt-in; instrumentation libraries ship with it off
and our own spans copy that behaviour. Without content the span still carries model and tokens, which makes it look
healthy while being useless for debugging. Switch it on with the standard variable and set the two attributes Opik
reads as the span's input and output:

```ts
// OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true
span.setAttribute("gen_ai.prompt", JSON.stringify({ messages }));
span.setAttribute("gen_ai.completion", JSON.stringify({ role: "assistant", content: answer }));
```

**Token counts land but `total_estimated_cost` is null.** Opik prices a span only when it recognises the
provider. Sending only `gen_ai.request.model` plus usage gave tokens and no cost; adding either
`gen_ai.system` or `gen_ai.provider.name` set to `openai` made the cost appear. Set both
(`gen_ai.provider.name` is the current name, `gen_ai.system` the older one).

**Traces never appear (or the last questions are missing) after a short script.** The batch span processor
sends spans on a timer, so a process that exits first drops them. Call `await shutdownTelemetry()` (which runs
`provider.shutdown()`) before exiting, and in a server do it in a SIGINT/SIGTERM handler.

## How it's put together

- `docs/` four fictional care guides (water parameters, tank mates, feeding, disease signs).
- `src/telemetry.ts` OTel provider, OTLP exporter and Opik headers, `withSpan`, the content-capture switch, flush/shutdown.
- `src/rag.ts` ingest, retrieve and answer, each as an OTel span with `gen_ai.*` attributes.
- `src/server.ts` the Hono app; opens the request span that roots each trace.
- `src/chunk.ts`, `src/retrieve.ts` markdown chunking and cosine top-k.
- `src/main.ts` runs the service; `src/demo.ts` boots it, asks five questions, shuts down and flushes.
- `src/check.ts` reads the project back from Opik and asserts usage, cost and text.
- `tests/care-rag.test.ts` offline vitest: chunking, ranking, prompt, HTTP validation, span attributes with a
  fake OpenAI client, and the content-capture switch, plus a run with tracing disabled.

*built with Opik · inspired by Opik's examples and documentation*
