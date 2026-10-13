# optimizer-plant-problem-classifier

**Let an optimizer rewrite a vague gardening prompt, and watch the score curve prove it.**

[![Python](https://img.shields.io/badge/python-3.12+-blue?style=flat)](pyproject.toml)
[![opik-optimizer](https://img.shields.io/badge/opik--optimizer-3.2.0-orange?style=flat)](https://github.com/comet-ml/opik)
[![setup](https://img.shields.io/badge/setup-uv-de5fe9?style=flat)](https://docs.astral.sh/uv/)

A gardener writes "my pothos is yellow and the soil smells sour". Which of six causes is it? Writing a prompt that answers *correctly and in a form your code can use* is mostly trial and error, and trial and error with no record is how teams end up unsure whether prompt v7 is really better than v3. This example hands the trial and error to Opik's Agent Optimizer and keeps the receipts.

## What you'll build

A classifier that labels a plant-problem description as one of `pests`, `disease`, `overwatering`, `underwatering`, `nutrient-deficiency` or `light`. It is checked against 24 invented gardener descriptions in `data/problems.json`, four per cause, and scored by exact match on the label.

The seed prompt is the sort of thing you write in thirty seconds: it lists the causes in plain English ("too much water", "a lack of nutrients") and asks for "a short phrase". gpt-4o-mini obliges with "Aphid infestation." and "Too much water.", which are sensible answers and almost never an exact label, so seed accuracy is about 0.00 to 0.04. `main.py` then runs `MetaPromptOptimizer` for at most 6 trials (gpt-4o-mini doing the classifying and the reasoning). It reads the misses, proposes candidate prompts, keeps the best, and saves it to the prompt library.

```
seed prompt -> score on 24 descriptions -> LLM reads the misses ("expected 'overwatering', model said 'Too much water.'")
            -> 3 candidate prompts per round -> score each -> keep the best (<= 6 trials) -> save to prompt library
```

## See it in Opik

Open the project `optimizer-plant-problem-classifier` (local Opik at http://localhost:5173, workspace `default`).

- **Optimization runs**: the newest run, objective `label_accuracy`, shows one point per trial. In the verified run the score sat at 0.00 for the seed, one candidate jumped to **0.417**, and the other candidates scored 0.00 to 0.04. A curve with a single spike is normal for six cheap trials. Click any trial to read the exact prompt it evaluated and the per-description results; each row carries a reason such as `expected 'light', model said 'Insufficient light.'`.
- **Prompts**: the prompt `plant-triage` has two versions. The first is the seed. The second, saved only because it beat the seed, tells the model to "respond with a single, clear term" and names the causes. Comparing the two is the whole lesson in one diff.
- **Traces**: 170 traces: 168 `evaluation_task` traces (7 scoring passes x 24 descriptions), each holding an `llm` span with token usage and an estimated cost (about $0.011 in total), plus 2 `optimization_algorithm` traces from the optimizer itself.
- **Dataset and experiments**: the dataset `plant-problem-descriptions` has 24 items, and its experiments list has 7 entries (the seed plus 6 trials), each with its accuracy.

## Run it yourself

1. `cp .env.example .env` and set `OPENAI_API_KEY` (or rely on a repo-root `.env`, which `main.py` loads). Local Opik needs no further configuration once `opik configure` has been run.
2. `uv sync`
3. `uv run main.py` takes about a minute and costs a few cents. Scores vary between runs because gpt-4o-mini and the optimizer's search are not deterministic.
4. Optional: `uv run baseline.py` scores the seed prompt alone and traces each call as a `classify_problem` trace, handy for seeing a single failing answer.
5. Open the project's **Optimization runs** tab.

## Poke around

- Add a seventh cause (for example `transplant-shock`) with a few rows in `data/problems.json` and see if the optimizer works out the new label.
- Raise `MAX_TRIALS` to 12 in `main.py` and check whether more trials beat 0.417 or just repeat themselves.
- Loosen `label_accuracy` in `plant_classifier.py` so "too much water" counts as `overwatering`, and see how quickly the seed passes.
- Remove the `reason` from `metric` in `main.py` and compare the curve (see the first gotcha).

## Gotchas we hit

**The optimizer never improves; every candidate scores 0.00 to 0.04.** The metric returned a bare float, so the optimizer's reasoning model saw that answers failed but not what they should have said, and it kept rewording the prompt without ever learning the label spellings. Return a `ScoreResult` with a `reason` that includes the expected label:

```python
ScoreResult(name="label_accuracy", value=score, reason=f"expected '{label}', model said '{answer}'")
```

## How it's put together

- `main.py`: dataset upload, the metric, seed prompt, the bounded `MetaPromptOptimizer` run, the prompt-library save.
- `plant_classifier.py`: the labels, seed prompt, exact-match scorer and the traced `classify` call.
- `baseline.py`: scores the seed prompt on its own, with traces.
- `data/problems.json`: 24 invented labeled descriptions.
- `tests/test_classifier.py`: offline tests for the dataset, the metric and a traced call with tracking disabled. Run `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`.

*built with Opik · inspired by Opik's examples and documentation*
