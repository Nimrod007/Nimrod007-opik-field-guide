<div align="center">

# langgraph-boardgame-rules-rag

**A rules referee for three invented board games, with every retrieval and answer visible in Opik.**

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/langgraph-1.2-1C3C3C?style=flat)
![Opik](https://img.shields.io/badge/opik-2.2.99-2f54eb?style=flat)

</div>

Rules questions are a sneaky RAG workload. "Can I raid a ship in Driftwood Quay?" has exactly one right answer, written in exactly one paragraph of one rulebook, and a model that grabs the wrong paragraph will still answer in a confident, referee-like voice. This project is a small referee bot that answers from three fictional rulebooks, and it is wired so you can see *which paragraphs it was shown* for every answer and whether changing retrieval makes the answers better or worse.

## What you'll build

- **Three invented rulebooks** in `rules/`: *Saltmarsh Traders* (a tidal trading race), *Emberfall Keep* (a co-op dungeon with a countdown clock) and *Tidecaller* (a two-player card duel). 18 sections in total, each section becomes one retrievable chunk.
- **A two-node LangGraph**: `retrieve` embeds the question (`text-embedding-3-small`) and pulls the top-k sections from an in-memory vector store, `generate` answers with `gpt-4o-mini` from those sections only, and says "the rulebooks do not cover it" when they don't.
- **A CLI** (`rulesrag ask`, `eval`, `demo`) over four modules: corpus, retriever, graph and evals.
- **An Opik dataset and experiments**: 15 rules questions (one deliberately unanswerable, three that need two sections to answer), scored by the `Hallucination` and `ContextPrecision` judges.

## See it in Opik

Run the demo, then open the **`langgraph-boardgame-rules-rag`** project.

**Traces.** The project holds 33 traces: 3 from the demo questions (named `LangGraph`) and 30 from the two experiments (named `evaluation_task`, 15 per experiment). Open one `LangGraph` trace and the span tree is `retrieve` containing a `search_rulebooks` span (type `tool`), then `generate` containing a `ChatOpenAI` span (type `llm`). The `search_rulebooks` output is the exact list of rule sections the model was given, such as "Saltmarsh Traders / Setup ...". For the question "Can I play Saltmarsh Traders with 5 players?" you can see the sections it was handed (the first is Setup) and that none states a player limit, and the answer, "The rulebooks do not cover it", is the right one. The `ChatOpenAI` span carries tokens and cost (about $0.0003 per question). The trace metadata also holds the graph definition, so the UI can draw `retrieve -> generate`.

**Experiments.** The **Experiments** page lists `k3-baseline` and `k1-thin-retrieval` on the `boardgame-rules-qa` dataset (15 items each). The config columns show `k`, and both score columns appear per row. In the run I verified:

| experiment | context_precision | hallucination |
|---|---|---|
| `k3-baseline` (3 sections) | 0.67 | 0.00 |
| `k1-thin-retrieval` (1 section) | 0.65 | 0.01 |

The gap is small, and honestly within judge noise (re-running `k3-baseline` during development moved context_precision by about 0.02). The rows are where the story is: with one section the cross-section question about raiding in Driftwood Quay while buying a pearl scored hallucination 0.2 (k=3: 0.0) because only half of the answer was on the page it saw. Select both experiments and press Compare to see rows side by side.

## Run it yourself

1. Install [uv](https://docs.astral.sh/uv/) and have Opik running locally (`opik configure`), or set `OPIK_API_KEY` and `OPIK_WORKSPACE` for Opik Cloud.
2. `cp .env.example .env` and set `OPENAI_API_KEY` (a `.env` in any parent directory also works).
3. `uv sync`
4. `uv run rulesrag demo` - asks three questions, then runs both experiments. About a minute, a few cents of OpenAI usage.
5. Or one piece at a time: `uv run rulesrag ask "How many Reefs can I have?"`, `uv run rulesrag eval -k 2 --name k2`.
6. Offline tests: `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`

## Poke around

- Run `uv run rulesrag eval -k 5 --name k5` and compare against `k3-baseline`. Does more context help, or does ContextPrecision drop as unrelated sections arrive?
- Edit a rule in `rules/tidecaller-cards.md` (say, change the Reef limit to 4) and ask about it. The answer follows the page, right or wrong, and the hallucination score stays 0: it measures faithfulness to the retrieved text, not truth.
- Add a question to `data/questions.json` and re-run `eval`; the dataset insert is deduplicated, so only the new row is added.
- Ask a question that names no game ("How many crystals can I hold?") and read the `search_rulebooks` output to see which game's section wins.

## Gotchas we hit

**1. `ImportError: cosine_similarity requires numpy to be installed` on the first question.** `InMemoryVectorStore` does its similarity search with numpy but `langchain-core` does not depend on it. Add `numpy` to your dependencies (it is in this project's `pyproject.toml`).

**2. The `retrieve` span is bare: no retriever span appears.** With `opik==2.2.99` and `langchain-core 1.6`, `OpikTracer` logged no span for the `as_retriever().invoke(...)` call, so the trace showed that the node ran but not what it searched for. Fix: wrap the search in a named function, `@opik.track(name="search_rulebooks", type="tool", ignore_arguments=["store"])`. It then appears nested under `retrieve` with the question and `k` as input and the chunks as output. `ignore_arguments` keeps the vector store object out of the logged input.

**3. Short scripts lose their last traces.** Traces are sent from a background thread, so a CLI that exits right after the last call can drop them. `rulesrag` calls `opik.flush_tracker()` before returning.

## How it's put together

- `rules/*.md` - the three fictional rulebooks; one `##` section becomes one chunk.
- `data/questions.json` - the 15 questions and expected answers behind the dataset.
- `rulesrag/corpus.py` - splits rulebooks into chunks.
- `rulesrag/retriever.py` - in-memory vector store and the tracked `search_rulebooks` function.
- `rulesrag/graph.py` - the retrieve -> generate LangGraph and its prompt.
- `rulesrag/tracing.py` - project name and the `OpikTracer` wrapping.
- `rulesrag/evals.py` - dataset creation and the Hallucination / ContextPrecision experiment.
- `rulesrag/cli.py` - `ask`, `eval` and `demo` commands.
- `tests/test_rulesrag.py` - chunking, retrieval, graph wiring with a fake model, question set, score formatting.
- `tests/test_tracing_disabled.py` - the traced graph still runs with `OPIK_TRACK_DISABLE=true`.

---

*built with Opik · inspired by Opik's examples and documentation*
