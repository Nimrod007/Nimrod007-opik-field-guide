# ollama-ham-radio-rag

*A handbook assistant for a radio club that answers entirely on your own machine, and still gives you a full trace of every answer.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![langchain-ollama](https://img.shields.io/badge/langchain--ollama-1.1-1C3C3C?style=flat)
![Opik](https://img.shields.io/badge/Opik-2.2.99-2f54eb?style=flat)

Tracing is usually sold alongside cloud models: you get token counts, cost, a provider name. What do you get when the model is a 1B-parameter file running on your laptop and no cloud LLM is called at all? This example answers that. It is a retrieval-augmented assistant over the (fictional) operating handbook of the Larkspur Valley Amateur Radio Club, and every model call, embedding included, goes to a local Ollama server. No provider key exists anywhere in the project. The only network traffic that leaves the process is the trace itself, which goes to Opik (cloud or self-hosted).

## What you'll build

- `docs/` holds four short chapters: band plans, call procedures, antenna basics, emergency-net etiquette. Each `##` section becomes one chunk.
- `nomic-embed-text` embeds the chunks into an in-memory vector store; `llama3.2:1b` answers from the top two sections.
- The chain is plain LangChain, traced by Opik's `OpikTracer` callback. Retrieval gets its own named span (see Gotchas for why that needs a decorator).

## See it in Opik

Open the **ollama-ham-radio-rag** project and the Traces tab. One run gives four traces named `ask_the_handbook`, tagged `ollama` and `local-rag`, one per question. Each trace holds seven spans: the `RunnableParallel` step, `search_handbook`, `RunnablePassthrough`, the prompt template, `ChatOllama` (type `llm`), `StrOutputParser`, and a tool span called `retrieve_sections`.

Open `retrieve_sections` and read its output: a list of the sections the vector store returned, each with its similarity score. For "What SWR is too high to keep transmitting?" it shows `Antenna Basics > Standing wave ratio` at 0.766 followed by `Band Plans... > 10-meter band layout` at 0.586, so you can see retrieval did its job. Then compare that to the `ChatOllama` span, which carries the exact prompt and the model's answer.

That comparison is the point. The first question, "Which frequency and tone do I use to reach the LV-2 repeater?", retrieves the right section (`2-meter band layout`, 0.69), yet the 1B model answers "146.010 MHz with a 88.5 Hz access tone". The handbook says the repeater *transmits* on 146.010 and *listens* on 146.610, so you should transmit on 146.610. Retrieval was fine, generation mixed up the direction; without the span you would only see "the local model is bad".

The `ChatOllama` span has no token usage and no cost: this integration path reports none for Ollama, so for a local pipeline the lesson is tracing, not cost accounting. A full run takes a few seconds once the models are loaded.

## Run it yourself

1. Run Ollama and pull the two models. Either install it natively from ollama.com, or use Docker:
   `docker run -d --name ollama -p 11434:11434 -v ollama:/root/.ollama ollama/ollama`
   then `ollama pull llama3.2:1b && ollama pull nomic-embed-text` (with Docker: `docker exec ollama ollama pull llama3.2:1b`, same for the embedding model).
2. `uv sync`
3. Point Opik at your instance: run `opik configure` (cloud or self-hosted), or set `OPIK_URL_OVERRIDE` and `OPIK_WORKSPACE`. Copy `.env.example` to `.env` only if Ollama is not on `localhost:11434`.
4. `uv run main.py`
5. Open the `ollama-ham-radio-rag` project in Opik.

## Poke around

- Add "Who pays the club dues?" to `QUESTIONS`: the handbook says nothing, and the `retrieve_sections` scores will be lower. Does the 1B model admit it does not know?
- Raise `TOP_K` in `handbook.py` to 4 and check whether the extra sections help or distract the model.
- Swap `CHAT_MODEL` for `llama3.2:3b` and compare the same questions side by side in the Traces table.
- Edit a number in `docs/` (say the repeater tone) and see the new value flow from the retrieved section to the answer.

## Gotchas we hit

**The retrieval step is missing, or shows up as one blob of text.** With only `OpikTracer`, the vector store's retriever run was not recorded in the langchain-core 1.6 / opik 2.2.99 combination: the `search_handbook` span held a concatenated string and nothing else, with no scores or section names. Wrap retrieval in a named tool span instead:

```python
@opik.track(name="retrieve_sections", type="tool")
def retrieve_sections(question: str) -> list[dict]:
    hits = store.similarity_search_with_score(question, k=TOP_K)
    return [{"section": section_label(d.page_content), "score": round(s, 3), "text": d.page_content} for d, s in hits]
```

Because `OpikTracer` keeps its spans on Opik's context stack, the decorated call nests inside the trace automatically.

**The `ChatOllama` span has empty usage and cost.** The LangChain integration extracts usage only for providers it knows, and Ollama is not among them. Nothing is wrong with your setup; judge local runs by latency and answer quality.

## How it's put together

- `main.py`: builds the store and the chain, defines the traced `retrieve_sections`, runs the questions, flushes the tracer.
- `handbook.py`: loads and chunks the docs, labels sections, formats the context; no model calls.
- `docs/`: the four fictional handbook chapters.
- `tests/test_handbook.py`: offline tests with a fake store and a stubbed chat model, including one that runs the traced retrieval with tracking disabled. Run: `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`.
- `.env.example`: the optional Ollama URL; no keys.

---

*built with Opik · inspired by Opik's examples and documentation*
