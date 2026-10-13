# llamaindex-syllabus-pdf-qa

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![LlamaIndex](https://img.shields.io/badge/LlamaIndex-0.14-6a4c93?style=flat)
![Opik](https://img.shields.io/badge/Opik-2.2.99-2f54eb?style=flat)

**Ask three course syllabi about late work and attendance, then see in Opik which syllabus each answer really came from.**

Students ask the same questions every term: *What is the late penalty? How many absences before my grade drops? Do I need the prerequisite?* Every syllabus answers them, with different numbers. A RAG bot that retrieves the right-sounding paragraph from the wrong course gives a confident, wrong policy, and the answer text alone will not tell you it happened.

This example answers those questions over three generated PDF syllabi (a CS course, a biology course, a history seminar) with LlamaIndex and `gpt-4o-mini`, records every query in Opik through the LlamaIndex callback handler, and checks the policies with an Opik test suite that reports pass or fail per question.

## What you'll build

A small package, `syllabus_qa`, with one sub-package per stage and a CLI on top:

- `pdfs/` writes three fictional syllabi to `data/syllabi/` with reportlab. They are committed as small fixtures and regenerated if missing.
- `index/` loads the PDFs, splits them into roughly 256-token chunks (about one policy section each) and builds an in-memory vector index with `text-embedding-3-small`.
- `qa/` answers a question with the top 4 chunks and a prompt that makes the model name the course it used. It also has a deterministic `citation_guard` that flags numbers in the answer that appear in no retrieved excerpt.
- `suite/` holds 8 policy questions, each with plain-language assertions ("the answer says CS 214 projects lose 10% per day late"), plus two assertions applied to every question: no invented numbers, and the answer comes from the course that was asked about.
- `cli.py` ties it together: `syllabus-qa pdfs | ask | suite | all`.

## See it in Opik

Open the **llamaindex-syllabus-pdf-qa** project. After one `syllabus-qa all` run it holds 13 traces.

- **`query` traces (4)**, one per demo question. Open one: a `retrieve` span (with an `embedding` span inside) shows the chunks that were fetched. Because all three syllabi have a late-work section, the `retrieve` output can mix chunks from several courses (for the BIO 150 attendance question the answer cites `bio150`, `hist310` and `cs214` files in that rank order), which is why the prompt asks the model to name its course. The `synthesize` span below it holds `templating` and the `llm` span with the full prompt, the answer, and tokens (about 1,000 per question, roughly $0.0002 each). When an answer quotes the wrong course, this tree shows whether retrieval put the wrong chunk first or the model picked the wrong one.
- **`index_construction` (1)**, the chunking and embedding of the three PDFs.
- **`evaluation_task` traces (8)**, one per suite question. Each contains `task`, then `query` (with the same retrieve and synthesize spans), then a `citation_guard` span of type guardrail, then the judge's `llm_judge` spans. The guardrail's output is the list of numbers in the answer that no excerpt supports; it was empty for all 8.

Then open **Evaluation > Test suites** (or the link the run prints) and the suite `llamaindex-syllabus-policy-suite`. The experiment from my run shows 8 of 8 questions passed, each row with its assertions and the judge's reasoning. The judge is an LLM, so a re-run can differ: on an earlier run, "Do I need HIST 200 to take HIST 310?" failed because the answer said HIST 200 is required but dropped the instructor-permission waiver that sat in the retrieved excerpt. That is exactly the kind of near-miss a per-question pass/fail view is for.

## Run it yourself

1. `cd llamaindex-syllabus-pdf-qa && cp .env.example .env` and set `OPENAI_API_KEY` (a key in a parent directory's `.env` is also picked up). With a local Opik install configured through `opik configure`, nothing else is needed.
2. `uv sync`
3. `uv run syllabus-qa all` (about 30 to 60 seconds, a few cents of OpenAI usage).
4. Open the `llamaindex-syllabus-pdf-qa` project in Opik, then the test suite run printed at the end.

Other commands: `uv run syllabus-qa ask "Is CHEM 101 required for BIO 150?"`, `uv run syllabus-qa suite`, `uv run syllabus-qa pdfs` (rewrites the PDFs).

Tests need no keys and no Opik server: `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`

## Poke around

- Change `TOP_K` in `syllabus_qa/config.py` from 4 to 1 and ask about CS 214 late work: with one chunk, check in the `retrieve` span whether it is still the right course.
- Edit a number in `pdfs/content.py` (make the BIO 150 late penalty 25%), run `syllabus-qa pdfs`, then `suite`. The assertion that pinned 15% fails and the judge says why.
- Delete the course code from the headings in `pdfs/render.py` and re-run. Chunks no longer say which course they belong to, so expect the "right course" assertion to get shakier.
- Ask something the syllabi do not cover ("When are CS 214 office hours?") and read the `llm` span: does the model say so or invent a time?

## Gotchas we hit

**Only the `evaluation_task` traces show up; the `query` and `index_construction` traces are missing, with `OPIK: No active LlamaIndex trace/span found in context` in the output.** `Settings.llm` and `Settings.embed_model` capture the callback manager that exists when they are created, and `set_global_handler("opik")` replaces it. Install the handler first, then create the models:

```python
set_global_handler("opik")      # first
Settings.llm = OpenAI(...)      # then the models
```

**The index answers from garbage: the "text" of the PDF starts with `%PDF-1.4`.** `llama-index-core` alone has no PDF parser and silently reads the file as raw bytes. The `llama-index` meta-package no longer bundles file readers either, so add `llama-index-readers-file` to your dependencies (this project does).

**The test run printed no errors but a Default Project appeared in Opik with `query` traces.** The LlamaIndex handler does not honour `OPIK_TRACK_DISABLE=true`, only `@opik.track` functions do. The offline tests therefore never call `set_global_handler`; the traced `citation_guard` is what they use to show that tracking can be off.

**Suite results mix in questions you never wrote.** `get_or_create_test_suite("name")` returns an existing suite with that name and `insert` adds to it. Pick a suite name unique to your project (this one is `llamaindex-syllabus-policy-suite`) or you will run, and judge, someone else's items.

## How it's put together

- `syllabus_qa/config.py`: project and suite names, model names, paths, `.env` loading.
- `syllabus_qa/pdfs/content.py`: the three syllabi as data. `render.py` turns them into byte-stable PDFs.
- `syllabus_qa/index/build.py`: chunking, embedding model, vector index.
- `syllabus_qa/qa/engine.py`: prompt, query engine, Opik handler, `ask`. `guard.py`: the traced numeric citation check.
- `syllabus_qa/suite/cases.py`: questions and assertions. `run.py`: builds the Opik test suite and runs it.
- `syllabus_qa/cli.py`, `__main__.py`: the command line.
- `data/syllabi/`: the committed fixture PDFs.
- `tests/test_syllabi.py`: PDF generation and fixture match, retrieval plumbing with mock models, number normalisation, and the traced guard with tracking disabled.

---

*built with Opik · inspired by Opik's examples and documentation*
