# smolagents-brewery-batch-analyst

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![smolagents](https://img.shields.io/badge/smolagents-CodeAgent-FFD21E?style=flat)
![Tracing](https://img.shields.io/badge/Opik-OpenInference%20%2B%20OTLP-2f54eb?style=flat)

*Ask a brewery's fermentation log a question, and read the pandas the agent wrote to answer it.*

## The problem

A code-writing agent answers with numbers, and a number looks the same whether it came
from the right groupby or a subtly wrong one. "Kestrel-12 stalls 94% of the time" is only
worth repeating if you can see the code that produced it. This example puts a smolagents
`CodeAgent` in front of the batch log of a fictional craft brewery, Tidewater Ferments, and
traces it into Opik so every generated snippet and every execution log is one click away.

## What you'll build

- `data/batches.csv`: 120 fermentation batches (gravity readings, temperature, yeast, fermenter, outcome) with two planted problems. Yeast strain `Kestrel-12` stalls (attenuation around 46% instead of 77%), and fermenter `FV-4` ran hot from July and produced only `off-flavor` batches.
- A `CodeAgent` on `gpt-4o-mini` that may import pandas and nothing else beyond smolagents' safe defaults.
- Three questions: which yeast attenuates worst, which fermenter ships off-flavor beer and since when, and average ABV per style.
- Tracing through OpenInference's `SmolagentsInstrumentor` and an OTLP exporter aimed at Opik. There are no decorators in the agent code.

## See it in Opik

Open the **smolagents-brewery-batch-analyst** project. The Traces tab holds three traces,
all named `CodeAgent.run`, one per question (a run takes roughly 4-7 seconds). Open the
yeast question and expand it: you get alternating `Step` spans (the think-code-observe
cycle) and `OpenAIModel.generate` spans, ending in a `FinalAnswerTool` span.

- Click an `OpenAIModel.generate` span. Its output is the assistant message: a short thought plus the pandas snippet in `<code>` tags. This is where you check *what the agent decided to compute*. Its metadata shows `gpt-4o-mini` and token usage (about 2.7k prompt tokens on the first call).
- Click the matching `Step` span. Its output starts with `Execution logs:` and holds exactly what the code printed, for example the `beer_style` / ABV table for question 3 (Stout 7.01, Saison 5.25, Hefeweizen 5.01, Lager 4.80, Pale Ale 4.48).
- The trace output is the final sentence, such as "Kestrel-12 ... 94.44% of its batches ended with the outcome 'stuck'", which you can reconcile against the log above it.

In my run the three traces had 18 spans in all: 6 `Step`, 6 `OpenAIModel.generate`, 3 `FinalAnswerTool`, and the 3 root `CodeAgent.run` spans.

## Run it yourself

1. Put `OPENAI_API_KEY` in `.env` (copy `.env.example`), or in a parent directory's `.env`. The code loads both.
2. Start Opik locally so it answers on `http://localhost:5173`. For another Opik URL set `OTEL_EXPORTER_OTLP_ENDPOINT`; see `tracing.py`.
3. `uv sync`
4. `uv run python main.py`
5. Open the project above in Opik. Total cost is about a cent of `gpt-4o-mini`.

Tests need no key and no Opik: `OPIK_TRACK_DISABLE=true uv run pytest`.

## Poke around

- Delete `"pandas"` from `additional_authorized_imports` in `main.py`, rerun, and watch the `Step` spans record the blocked import and how the agent recovers.
- Ask something the CSV cannot answer ("which brewer made the most batches?") and read how the agent reacts when no column fits.
- Run `make_data.py` after changing the seed or planting a third problem (say a cold lager fermenter), then see whether the agent finds it.
- Compare the prompt token count of the first and last `generate` span in a trace: each step re-sends the accumulated observations.

## Gotchas we hit

**Cost is empty on every span.** `usage` is filled (prompt, completion, total) but `total_estimated_cost` is `null`. Cause: raw OTLP spans carry no `provider` Opik recognises, so it cannot price them. Fix: nothing needed for this lesson; usage is real, and the dollar figure is derived (this run was about $0.01). To get cost, map a provider attribute onto the spans.

**Trace token total is double what the model used.** The trace showed 10,460 tokens while the two `generate` spans added up to 5,230. Cause: the instrumentor types `CodeAgent.run` as an `llm` span and repeats the summed usage on it, so the trace total counts it twice. Fix: read token counts from the `OpenAIModel.generate` spans (or the root span), not the trace-level total.

**`CodeAgent.run` shows up as an `llm` span.** Do not be surprised that the root-level agent span is typed `llm`; it is the same instrumentor behaviour as above, and the real model calls are the `OpenAIModel.generate` children.

## How it's put together

- `main.py`: builds the `CodeAgent`, asks the three questions, flushes tracing.
- `tracing.py`: OTLP exporter pointed at Opik with the project header, plus the instrumentor and the flush.
- `brewery.py`: CSV loader, ABV and attenuation maths, the briefing and the questions.
- `make_data.py`: seeded generator that rebuilds `data/batches.csv`.
- `data/batches.csv`: the committed batch log.
- `tests/test_brewery.py`: offline tests for the ABV formula, both planted problems, the tracing-off path, and `ask` against a stub agent.

---
*built with Opik · inspired by Opik's examples and documentation*
