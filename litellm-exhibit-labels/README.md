# litellm-exhibit-labels

*Wall labels for an invented natural-history museum, written by two models through one LiteLLM call, priced and timed in one Opik table.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![LiteLLM](https://img.shields.io/badge/litellm-1.79%2B-1C7ED6?style=flat)
![Opik](https://img.shields.io/badge/opik-2.2.99-2f54eb?style=flat)

A curator's question sounds simple: could the cheaper model write these labels just as well? To answer it you need what each call cost and how long it took, per model, from the same traffic. Two providers means two SDKs and two response shapes, so the numbers usually end up in a spreadsheet nobody trusts. Here the Hall of Deep Time at the (fictional) Aldermere Museum of Natural History needs six wall labels, and each is written by `gpt-4o-mini` and by `claude-haiku-4-5` using the identical prompt. LiteLLM's `OpikLogger` callback records every call, and a small script then reads the numbers back out of Opik and lines the two models up.

## What you'll build

- `data/artifacts.json`: six invented exhibits (a lantern-moth fossil, a marsh stilt-strider skeleton, beetle amber, and so on), each with a handful of facts.
- `labels.py`: builds the label prompt (60-word limit, "use only the facts above") and formats a local summary table.
- `main.py`: loops over both models and all six artifacts with `litellm.completion()`. The model is just a string, so a third provider is one more entry in `MODELS`. It registers Opik's callback, tags every call with the model short name and the artifact id, prints a table from the responses, and then prints a second table queried back from Opik.
- `compare.py`: groups the stored LLM spans by model and reports calls, tokens, estimated cost, how many spans were priced, and mean latency.

## See it in Opik

Open the project `litellm-exhibit-labels` (local Opik at http://localhost:5173). The Traces tab has 12 rows, one per completion, named `chat.completion`, each with a single `llm` span. The span carries the full prompt, the label the model wrote, token usage, `provider` and `model`, and an estimated cost. In my run the dated model names Opik stored were `gpt-4o-mini-2024-07-18` and `claude-haiku-4-5-20251001`.

Sort the table by estimated cost and the two models separate cleanly: the `gpt-4o-mini` traces cost about $0.00007 each, while the Haiku traces sit between $0.00051 and $0.00064. Added up for the six labels that was $0.000416 versus $0.003449, about 8.3x. Token totals were close (1,313 vs 1,445), so most of the gap is Haiku's higher per-token price. Latency was nearly a tie, 1.32 s vs 1.49 s on average. Filter by the tag `claude-haiku-4-5` or `gpt-4o-mini` to isolate one model, or by an id such as `A-103` to see both models' labels for the same amber. The same tags also let you check word counts by eye: both models mostly honored the 60-word limit (mean 54.8 and 51.5 words).

The last block of the script output is that same table, rebuilt from Opik's data rather than from local timers:

```
Model (as stored in Opik)    Provider   Calls  Tokens  Cost (USD) Priced  Mean latency
claude-haiku-4-5-20251001    anthropic      6    1445 $  0.003449   6/6          1.49s
gpt-4o-mini-2024-07-18       openai         6    1313 $  0.000416   6/6          1.32s
```

The `Priced` column is there on purpose: it reads `6/6` when Opik could price every span, and would show fewer if a model had a null cost.

## Run it yourself

1. Put `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` in a `.env` here or at the repo root (see `.env.example`). A local Opik needs no key; `~/.opik.config` or `OPIK_URL_OVERRIDE` points at it.
2. `uv sync`
3. `uv run main.py`  (about 20 seconds, well under one cent)
4. Open the `litellm-exhibit-labels` project in Opik, or re-print the Opik-side table any time with `uv run compare.py`.
5. Offline tests: `env -u OPENAI_API_KEY -u ANTHROPIC_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`

Each run adds 12 traces, and `compare.py` sums everything in the project, so delete earlier traces before a re-run if you want per-run totals.

## Poke around

- Add `"gemini-flash": "gemini/gemini-2.0-flash"` to `MODELS` (with a `GEMINI_API_KEY`) and re-run; nothing else changes and a third row appears in the table.
- Change `WORD_LIMIT` to 25 and compare how the models' token counts, and so the cost gap, move.
- Edit the prompt in `build_prompt` to ask for a title only, and watch output tokens, and which model is cheaper, change.
- In Opik, read both labels for `A-102` side by side and decide whether the pricier one is worth it.

## Gotchas we hit

- **Symptom:** the script starts with `LiteLLM:ERROR ... Asynchronous processing not initialized as we are not running in an async context no running event loop`, plus a `coroutine 'CustomBatchLogger.periodic_flush' was never awaited` warning. **Cause:** `OpikLogger.__init__` tries to start a background flush task and there is no event loop in a plain script. It then falls back to sending each call synchronously, so traces still arrive. **Fix:** silence just that noise while creating the callback:
  ```python
  logging.getLogger("LiteLLM").setLevel(logging.CRITICAL)
  warnings.filterwarnings("ignore", message=".*periodic_flush.*", category=RuntimeWarning)
  litellm.callbacks = [OpikLogger()]
  logging.getLogger("LiteLLM").setLevel(logging.WARNING)
  ```
- **Symptom:** filtering Opik by model `gpt-4o-mini` finds nothing. **Cause:** the span's `model` is the provider's dated name (`gpt-4o-mini-2024-07-18`, `claude-haiku-4-5-20251001`), not the string you asked for. **Fix:** pass your own short names as tags, as `main.py` does with `metadata={"opik": {"tags": [short_name, artifact["id"]]}}`.

## How it's put together

- `main.py`: runs both models over all artifacts, registers `OpikLogger`, flushes, prints both tables.
- `labels.py`: prompt builder, call record, local summary and table formatting.
- `compare.py`: reads llm spans back from Opik and groups them per model.
- `data/artifacts.json`: the six fictional exhibits.
- `tests/test_labels.py`: offline tests for data, prompt, summaries, the Opik grouping (including an unpriced span), and `write_label` with a stubbed completion and tracking disabled.
- `pyproject.toml`, `.env.example`, `.gitignore`: uv project and config.

---
*built with Opik · inspired by Opik's examples and documentation*
