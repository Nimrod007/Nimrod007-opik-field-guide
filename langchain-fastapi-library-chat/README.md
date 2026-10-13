# langchain-fastapi-library-chat

*A library chat widget's FastAPI backend, where every conversation shows up in Opik as a readable transcript.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?style=flat&logo=fastapi&logoColor=white)
![LangChain](https://img.shields.io/badge/langchain--core-1.x-1C3C3C?style=flat)
![Opik](https://img.shields.io/badge/opik-2.2.x-2f54eb?style=flat)

A chat widget talks to your backend one HTTP request at a time. A patron who asks three questions
produces three `POST /chat` calls, and by default your tracing sees three unrelated traces. When
someone says "the assistant kept suggesting romance after I asked for a mystery", you need turns one
through three side by side, as the patron saw them. This example is the backend for the fictional
Harbor Street Public Library's book-recommendation widget, traced so that each patron conversation
is a single Opik thread.

## What you'll build

- A FastAPI app with one endpoint, `POST /chat`, taking `{message, session_id}` and returning `{reply}`.
- A LangChain chain per turn: look up the patron's history and search the 14-book catalog in
  `data/catalog.json` (a keyword retriever, no embeddings, no network), format a prompt, call
  `gpt-4o-mini`, parse to a string.
- The chain takes the patron's text as a **plain string** and returns the reply as a **plain string**,
  so the root of every trace is just "what the patron said" and "what the bot answered".
- An `OpikTracer` created per request with `thread_id=session_id`, which is what stitches turns together.
- `main.py`, which boots the server in-process, plays two scripted three-turn conversations over HTTP,
  and shuts down.

## See it in Opik

Run it, then open the **langchain-fastapi-library-chat** project.

- **Threads tab:** two threads, `visitor-cozy-weekend` and `visitor-kids-science`, three turns each.
  Opening one reads like a chat log: for example the cozy-weekend thread starts with "Hi! I want
  something cozy and small-town for a snowy weekend." and the bot's answer recommending *Snowed In at
  Wren Hollow*, then the follow-up "Anything less romantic? More of a mystery." answered with *Salt and
  Static*.
- **Traces tab:** six traces named `library-chat-turn`, each carrying prompt and completion tokens
  and a dollar cost (about 360 prompt tokens and $0.00008 per turn in our run; prompt size grows as
  history accumulates).
- **Inside a trace:** five spans: `load-history-and-search` (general), under it `search-catalog` (a
  **tool** span whose output is the books that matched), then `ChatPromptTemplate`, `ChatOpenAI` (the
  **llm** span with token usage and cost) and `StrOutputParser`. Open `search-catalog` to see why the
  bot suggested a book. On the follow-up "Is the first one you mentioned on the shelf?" the retriever returns two loosely
  related books and the bot still answers from history, which is exactly the kind of thing the tool span makes visible.

## Run it yourself

1. `cd langchain-fastapi-library-chat`
2. Put `OPENAI_API_KEY` in `.env` (copy `.env.example`), or rely on a repo-root `.env`.
3. Point Opik at your instance (`opik configure`, or `OPIK_URL_OVERRIDE` for a self-hosted stack).
4. `uv run main.py` (about 20 seconds, a fraction of a cent).
5. Open the project's **Threads** tab.

Tests, offline and keyless: `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`.

To use the endpoint yourself: `uv run uvicorn app:app --port 4170`, then
`curl -X POST localhost:4170/chat -H 'content-type: application/json' -d '{"message":"cozy mystery?","session_id":"me"}'`.

## Poke around

- Reuse a `session_id` across two curl calls, then change it: the thread count in Opik follows the id.
- Ask for something not in the catalog ("a cookbook") and check `search-catalog`'s empty output and
  how the bot handles it.
- Add a field to `catalog.json` and watch it appear in the `ChatOpenAI` span's input.
- Replace the string-in chain with one taking a dict (`{"message": ...}`) and compare how the
  thread transcript renders.

## Gotchas we hit

**Retrieval is missing from the trace tree.** Symptom: the chain looks fine but there is no span for
the catalog search. Cause: with `opik 2.2.99` and `langchain-core 1.6.10`, a `BaseRetriever` run
executed under `OpikTracer` produced no span at all (a scratch chain `retriever | lambda` showed only the
lambda). Fix: do the search in a plain function decorated
`@opik.track(name="search-catalog", type="tool", project_name=PROJECT_NAME)` and call it from a chain step;
it nests under the chain as a tool span.

**Traces vanish at exit.** The SDK sends from a background thread, so `main.py` ends with
`opik.flush_tracker()`.

## How it's put together

- `app.py`: FastAPI app, chain, per-session history, tracer and tool-span wiring.
- `catalog.py`: catalog loading, keyword scoring, formatting for the prompt.
- `data/catalog.json`: the fictional 14-book catalog.
- `main.py`: boots uvicorn, plays the scripted conversations, flushes Opik.
- `tests/test_app.py`: retrieval, formatting, the endpoint with a fake model, and a traced function with tracking disabled.

---

*built with Opik · inspired by Opik's examples and documentation*
