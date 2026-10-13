# anthropic-ts-espresso-manual-qa

**An espresso-machine manual bot that must quote the manual word for word, and a test suite that checks every quote.**

![TypeScript](https://img.shields.io/badge/TypeScript-strict-3178C6?style=flat&logo=typescript&logoColor=white)
![Anthropic SDK](https://img.shields.io/badge/%40anthropic--ai%2Fsdk-0.133-191919?style=flat)
![Opik](https://img.shields.io/badge/opik-2.2.99-2f54eb?style=flat)

If you tell someone their machine's boiler is "probably fine" after an E7 error, and the manual actually says to
unplug it and call support, the bot just gave bad safety advice. Manual and policy bots are risky in one specific
way: an answer that sounds right but is not in the document. This example makes Claude (Haiku 4.5, through
`@anthropic-ai/sdk`) wrap every claim in a `<quote>` copied from a fictional owner's manual (the *Brasa Lumina 7*),
then turns "are the quotes real?" into an Opik test suite written in plain English.

## What you'll build

- `docs/manual.md`: a short invented owner's manual (safety, brewing, descaling, error codes, warranty).
- `src/qa.ts`: the Q&A function. The whole manual goes in the system prompt, and the rules demand verbatim `<quote>`
  tags.
- `src/tracing.ts`: hand-rolled Opik tracing for the Anthropic call. **There is no official Opik integration for the
  Anthropic TypeScript SDK** (Python has `track_anthropic`; npm has no `opik-anthropic`), so this file wraps
  `messages.create` with `track()` as an `llm` span and fills in model, provider and token usage itself.
- `src/suite.ts`: a test suite with three global assertions, four item-level ones, and a seventh item the manual
  cannot answer. The suite runs through Opik's exported `runTests`. Each item runs three times and must pass twice.

Question -> Claude answers with quotes -> an LLM judge (Haiku again, so one API key) checks every assertion -> pass or
fail per question, stored as one Opik experiment.

## See it in Opik

Open the **anthropic-ts-espresso-manual-qa** project.

**Traces.** After one run there are 22 traces: the single demo answer, plus 21 from the suite (7 questions x 3 runs).
The demo trace is `answer_question` (a `general` span) with one `anthropic.messages.create` child of type `llm`. It
shows model `claude-haiku-4-5-20251001`, provider `anthropic`, about 1,000 input tokens (the manual rides along on
every call) and an estimated cost around $0.0015. Suite traces are rooted at `llm_task`, with the same
`answer_question` tree nested inside, plus an `llm_judge` span for each assertion pass. Across the run Opik
estimated about $0.10 over 43 `llm` spans, and every one of them has a cost.

**Test suite.** Open the suite named `anthropic-ts-espresso-manual-qa` and its experiment `espresso-qa-strict`: 7 items,
7 passed. Each row is a question with a hard pass or fail plus per-assertion scores. When something fails, the judge's
reason is attached ("the quoted excerpt does not appear verbatim..."), and you can click through to the trace with the
exact prompt and answer.

## Run it yourself

1. Local Opik running, then `export OPIK_URL_OVERRIDE=http://localhost:5173/api/ OPIK_WORKSPACE=default`
   (for Opik Cloud also set `OPIK_API_KEY` and the cloud URL).
2. `cp .env.example .env` and set `ANTHROPIC_API_KEY` (a `.env` one directory up also works).
3. `npm install`
4. `npm run demo` (about 40 seconds, roughly $0.10)
5. Open the project in Opik, then the suite's newest experiment.

Tests need no keys: `npm test` (sets `OPIK_TRACK_DISABLE=true`, the SDK's switch that turns `track()` into a
pass-through).

## Poke around

- **Sabotage the prompt.** `QA_PROMPT=loose npm run demo` swaps the strict rule for "condense and reword the
  excerpt". The run is named `espresso-qa-loose`. In our run the double-basket question failed 0 of 3 times: the
  judge pointed at a quote that was a rewording of "Use 18 grams of ground coffee for the double basket...". Compare
  the two experiments.
- **See the execution policy hide noise.** With a milder loose wording, one run in 21 slipped but the item still
  passed, because it only needs 2 of 3. Set `globalExecutionPolicy` in `src/suite.ts` to `runsPerItem: 1` and the same
  slip becomes a failed item.
- **Add an assertion that must fail**, e.g. "The response contains no `<quote>` tags", with
  `suite.updateTestSettings({ globalAssertions: [...] })`. Every item flips to failed, each with a reason.
- **Add a trap question** the manual cannot answer ("Is it dishwasher safe?") with its own assertion, like the 110V
  item already does.

## Gotchas we hit

**1. `SyntaxError: The requested module 'opik' does not provide an export named 'SpanType'`.** The typings
declare `SpanType`, so `tsc` is happy, but at runtime ESM only exports it as `OpikSpanType`. Pass the string
instead: `track({ type: "llm" }, fn)`.

**2. The root span is labelled `llm` and has no tokens.** `track()` without a `type` defaults to `llm`, so your
wrapper function looks like a model call. Set `type: "general"` on any function that is not itself the model call.

**3. The `llm` span has no cost.** Cost is derived from provider, model and usage. Return them from `enrichSpan`:
`{ model, provider: "anthropic", usage: { prompt_tokens, completion_tokens, total_tokens } }`. We map
Anthropic's `input_tokens` / `output_tokens` to those names by hand.

## How it's put together

- `src/qa.ts`: system prompt, quote helpers, `answerQuestion` (traced).
- `src/tracing.ts`: `traceMessages`, the manual Anthropic wrapper that emits the `llm` span.
- `src/questions.ts`: questions, global and item assertions.
- `src/suite.ts`: creates the test suite and calls `runTests`.
- `src/main.ts`: one demo answer, then the suite, then a pass/fail summary and a flush.
- `src/env.ts`: loads `.env`.
- `docs/manual.md`: the fictional manual.
- `tests/qa.test.ts`: offline tests for quote extraction, prompt contents, and traced functions with tracking off.

---

*built with Opik · inspired by Opik's examples and documentation*
