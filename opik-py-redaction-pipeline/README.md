# opik-py-redaction-pipeline

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![Opik](https://img.shields.io/badge/opik-2.2.99-2f54eb?style=flat)
![Model](https://img.shields.io/badge/model-gpt--4o--mini-412991?style=flat)

*Scrub personal data out of documents, and hand-build every Opik trace, span, cost and score along the way.*

Redaction is a pipeline where a silent miss is worse than a crash: one email address that slips through is a leak, and the output still looks fine. You want to see, per document, which step found what, what the model cost, and whether the result was actually clean. Decorators and integrations would hide those choices, so this example uses none. It drives the low-level Opik client (`client.trace()`, `trace.span()`, explicit `usage`, `log_feedback_score()`) so each field in Opik is one call you can point at.

## What you'll build

A script that redacts six fictional documents (support tickets, an HR note, an email, an incident report) in five steps:

```
redact-document            trace   (client.trace)
  regex-prepass            tool        emails, phones, SSNs, cards, IPs
  chat gpt-4o-mini         llm         names, addresses, birth dates, home towns
  merge                    general     union, dedupe, drop strings inside longer ones
  redact                   general     replace with [LABEL] placeholders
  verify                   guardrail   rescan the output; any survivor is a leak
feedback scores on the trace: pii_recall (vs. known truth), verify_passed
```

Each document ships with the list of PII strings it contains, so the run can score itself. One document (`d6`) hides an email as "priyanka dot nandakumar at lindenwick dot example". No regex matches it and the model is told to ignore emails, so it survives. The pipeline's own `verify` step cannot see it either. Only the ground-truth `pii_recall` score notices.

## See it in Opik

Open the `opik-py-redaction-pipeline` project and the Traces tab. There are six `redact-document` traces, each under a second long, each with a `pii_recall` and a `verify_passed` column. Five rows read 1.0 and 1.0. The `d6` row reads `pii_recall` 0.5 next to `verify_passed` 1.0, and all six are tagged `verified`. That row is the point: a check you wrote yourself can pass on a leak, and a score against known truth is what catches it. Hover the 0.5 and the reason lists the string that is still in the output.

Expand any trace for five spans. `regex-prepass` has a tool icon and shows its findings. `chat gpt-4o-mini` is the llm span: input messages, the raw JSON the model returned, and, in the usage and cost columns, about 150 prompt tokens, 20 completion tokens, and a cost near $0.00003. The model shows as `gpt-4o-mini-2024-07-18` with provider `openai`. `verify` carries the guardrail icon. Across the six traces the project holds 30 spans, 1,152 LLM tokens and $0.00027 of estimated cost; sort by `pii_recall` to put `d6` first.

## Run it yourself

1. Install uv, then `cd opik-py-redaction-pipeline`.
2. `cp .env.example .env` and set `OPENAI_API_KEY` (a repo-level `.env` one directory up is read too).
3. Point Opik somewhere: a local self-hosted stack works through `~/.opik.config`, or export `OPIK_API_KEY` for a cloud workspace.
4. `uv run main.py`. It takes about 6 seconds and costs a fraction of a cent.
5. Open the project in Opik as described above.
6. Tests need no keys and no server: `env -u OPENAI_API_KEY -u ANTHROPIC_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`

## Poke around

- Add an obfuscated-email pattern to `PATTERNS` in `pipeline.py` and rerun: `d6` goes to 1.0, and the `regex-prepass` span now shows what it caught.
- In `traced_pipeline.py`, delete `provider="openai"` from the llm span. Tokens still show, the cost cell goes empty.
- Replace `record(...)` with `span = trace.span(...)` followed by `span.end(output=...)` for the fast steps and run it a few times (see the first gotcha).
- Add a `verify` rule that fails when a `[NAME]` placeholder appears next to a capitalised word. Watch `verify_passed` start moving.

## Gotchas we hit

**"Calling Span.end() shortly after creation with batching enabled may cause data loss", and rows with no name.** The SDK queues a create and an update separately. For a fast step the update can reach the server first, which then stores a nameless row with only the update's fields. In a loop of 30 traces, each with one span and `span.end()` called straight after creation, 3 traces and 3 spans came back nameless and without input. Fix: send a span once and complete, `trace.span(name=..., start_time=t0, end_time=now, output=...)`, as `record()` does here. For the trace, re-send the full payload with the same id (`client.trace(id=trace.id, ..., end_time=..., output=...)`). The backend overwrites the row; with this the six traces all had name, input, output and duration.

**The trace shows tokens but the cost is empty.** Cost is computed from `model`, `provider` and `usage` together. Set `provider="openai"` (a string the pricing table knows) and pass `prompt_tokens`, `completion_tokens` and `total_tokens` on the llm span. Using `response.model` (`gpt-4o-mini-2024-07-18`) priced correctly.

**Flush: what a normal exit does and what it does not.** With default batching, a script that simply ends still delivered its trace (the SDK flushes on interpreter exit, verified by a one-off test). A hard exit (`os._exit`, a kill, a crash) delivered nothing. Call `client.flush()` explicitly, as `main.py` does, so delivery does not depend on how the process dies, and so you can query right afterwards.

**`OPIK_TRACK_DISABLE=true` and traces still show up.** That setting only turns off `@track` and the integrations. A hand-built `client.trace()` ignores it: running the test suite with the variable set still created a trace in the project. The fix is a guard at the top of the traced function, `if not opik.is_tracing_active(): return steps.process_document(...)`, which also honours `opik.set_tracing_active(False)`.

## How it's put together

- `pipeline.py` - the untraced logic: regex patterns, prompt, parsing, merge, redact, verify, recall scoring.
- `traced_pipeline.py` - the same flow with every Opik call written by hand: trace, five spans, usage, scores.
- `main.py` - loads the documents, runs them, prints recall per document, flushes.
- `data/documents.json` - six fictional documents with their ground-truth PII lists.
- `tests/test_pipeline.py` - offline tests for the steps, plus one that runs the traced function with tracking disabled and a stub model.

---

*built with Opik · inspired by Opik's examples and documentation*
