# vercel-ai-sveltekit-stargazing-chat

*A streaming stargazing assistant in SvelteKit whose every reply is traced, threaded and judged in Opik.*

![TypeScript](https://img.shields.io/badge/typescript-6-3178C6?style=flat&logo=typescript&logoColor=white)
![SvelteKit](https://img.shields.io/badge/sveltekit-3-FF3E00?style=flat&logo=svelte&logoColor=white)
![Vercel AI SDK](https://img.shields.io/badge/ai%20sdk-7-000000?style=flat&logo=vercel&logoColor=white)
![opik-vercel](https://img.shields.io/badge/opik--vercel-2.2.99-2f54eb?style=flat)

A streamed answer is not a return value. The text leaves your server token by token, the browser re-sends the whole conversation on every request, and nothing in your handler ever holds "the answer" in one piece, so ordinary logging either misses it or drowns in duplicate history. This example wires a SvelteKit chat to Opik so that each streamed turn becomes one finished trace, turns of the same chat collapse into a thread, and a server-side LLM judge scores every new trace without any scoring code in the app.

## What you'll build

"Nova" is the assistant for a fictional backyard-astronomy club. It answers questions about a made-up sky-events calendar (`data/sky-events.json`: meteor showers, a comet, Jupiter at opposition, a lunar eclipse) through a `lookupSkyEvents` tool, using `gpt-4o-mini`.

- `src/routes/+page.svelte` is the chat UI, built on the `Chat` class from `@ai-sdk/svelte`.
- `src/routes/api/chat/+server.ts` calls `streamText` with the tool and a `runtimeContext` that carries the chat id.
- `src/lib/telemetry.ts` registers the `OpikExporter` from `opik-vercel` and the AI SDK's OpenTelemetry integration. `src/hooks.server.ts` loads it at startup.
- `scripts/demo.mjs` does everything in one command: creates the online-evaluation rule if needed, builds and boots the server, plays three scripted two-turn streaming conversations, shuts the server down so spans flush, then waits for the judge's scores.

## See it in Opik

Open the project `vercel-ai-sveltekit-stargazing-chat`. After one demo run the Traces tab holds six `stargazing-turn` traces (one per streamed reply) plus six traces named `online_evaluation`, which are the judge's own runs landing in the same project. Open a `stargazing-turn` trace and the tree shows an `llm` span (`chat`, `gpt-4o-mini`) that decides to call the tool, a `tool` span `execute_tool lookupSkyEvents` whose input is the model's arguments (for example `{"keyword":"lunar eclipse"}`) and whose output is the matching calendar rows, then a second `llm` span with the final answer. Each llm span has prompt and completion tokens and an estimated cost; across the six turns the chat model cost about $0.0008. The trace is complete even though the response left the server as a stream.

The Threads tab shows three threads, each with two traces: the Leonid shower conversation, the Jupiter-and-lunar-eclipse conversation, and one where the calendar has no total solar eclipse and Nova says so before turning to telescope advice. The thread id is the chat id the browser sends with each request.

In the feedback-score column of the traces, each `stargazing-turn` carries `answer_relevance = 1`, written by the online-evaluation rule `stargazing_answer_relevance` (Online evaluation tab of the project). The rule samples 100% of new traces, hands the trace input and output to a `gpt-4o-mini` judge, and attaches a 0/1 score. In the verified run all six traces were scored.

## Run it yourself

1. Start a local Opik and make sure an OpenAI key is registered in its provider settings (the judge runs inside Opik, not in this app). The demo checks this and stops with a message if it is missing.
2. `cp .env.example .env` (or keep keys in a `.env` one folder up) and set `OPENAI_API_KEY`. For a local Opik also export `OPIK_URL_OVERRIDE=http://localhost:5173/api/` and `OPIK_WORKSPACE=default`; these are in `.env.example`.
3. `npm install`
4. `npm run demo` (about 35 seconds). Or `npm run dev -- --port 4192` and chat at http://localhost:4192 (not 5173, which a local Opik uses).
5. Open the project in Opik: Traces, then Threads, then Online evaluation.

Offline tests: `OPIK_TRACK_DISABLE=true npm test` (no provider keys needed).

## Poke around

- Ask Nova about something the calendar lacks ("when is the next total solar eclipse?") and compare its answer and score with a question the calendar covers.
- Edit the judge prompt of `stargazing_answer_relevance` in the Opik UI to be stricter (for instance, require a date in the answer) and re-run the demo: new traces get the new behaviour, old ones keep their scores.
- Run `npm run dev -- --port 4192` and open it in two browser tabs: each tab has its own chat id, so each becomes its own thread.

## Gotchas we hit

**The project stays empty although the app answers fine.** In AI SDK v7 telemetry is not emitted automatically any more. Register an integration once at startup, after starting the exporter:

```ts
registerTelemetry(new OpenTelemetry({ usage: true, enrichSpan: ({ runtimeContext }) => ({ /* ... */ }) }));
```

The thread id has to be passed through `runtimeContext` in `streamText` and copied to the `ai.telemetry.metadata.threadId` attribute in `enrichSpan`, otherwise traces appear but without threads.

**`npm install` fails with `ERESOLVE ... peer opik@"^1.8.75" from opik-vercel`.** `opik-vercel` still declares an old peer range. Add to `package.json`: `"overrides": { "opik-vercel": { "opik": "$opik" } }`.

**`fetch failed: bad port` from the demo script.** Node's `fetch` refuses some ports as unsafe, and 4190 is one of them. The demo defaults to 4191.

**`$lib` import fails the build with `module_removed_lib`.** SvelteKit 3 dropped the `$lib` alias and `svelte.config.js`; this example uses relative imports and passes the adapter in `vite.config.ts`.

**Online-evaluation scores never appear.** The rule needs an OpenAI key in Opik's server-side provider store, and it must exist before the traces arrive (Opik does not back-score older traces). The demo creates the rule first and fails loudly if the key is missing. When re-running, delete only traces, not the rule.

## How it's put together

- `src/lib/telemetry.ts`: OpikExporter + AI SDK telemetry registration, flush on shutdown.
- `src/hooks.server.ts`: loads `.env` files and starts telemetry before the first request.
- `src/routes/api/chat/+server.ts`: `streamText` route with the calendar tool and thread context.
- `src/routes/+page.svelte`: the `Chat` class UI.
- `src/lib/sky.ts`: calendar loading, search and the system prompt.
- `data/sky-events.json`: the fictional calendar.
- `scripts/ensure-rule.mjs`: idempotent creation of the online-evaluation rule via REST.
- `scripts/opik-rest.mjs`: small REST helper used by the demo only.
- `scripts/demo.mjs`: rule, build, boot, scripted conversations, shutdown, score check.
- `tests/sky.test.ts`: offline tests for search and for the span-attribute helper.

---

*built with Opik · inspired by Opik's examples and documentation*
