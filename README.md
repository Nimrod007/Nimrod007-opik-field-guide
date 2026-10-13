# Opik field guide

**Twenty-one small LLM apps, each built to make one Opik feature obvious.**

![examples](https://img.shields.io/badge/examples-21-2f54eb) ![python](https://img.shields.io/badge/python-13-3776ab) ![typescript](https://img.shields.io/badge/typescript-8-3178c6) ![license](https://img.shields.io/badge/license-Apache--2.0-green)

Most tracing demos stop at "here is a trace." These apps go a step further. Each one has a real job (answer from a manual,
triage an insurance claim, review a grant application) and a concrete moment you can look at in
[Opik](https://github.com/comet-ml/opik): a handoff between agents, a retry that failed first, a prompt version that
took a test suite from 0% to 100%, a dollar figure that only appears once an attribute is mapped.

Each app runs on its own data, which is fictional and ships in the folder, and logs to its own Opik project
named after the folder. Every README reports numbers from a real run, including the parts that didn't work.

## Pick a trail

### Agents and multi-step work

| Example | Stack | What to look at in Opik |
|---|---|---|
| [openai-agents-insurance-claims](openai-agents-insurance-claims/) | Python · OpenAI Agents SDK | Triage hands off to specialists; handoff and tool spans, turns grouped into threads |
| [crewai-theater-season-planner](crewai-theater-season-planner/) | Python · CrewAI | One trace per kickoff, with tokens and dollars rolled up per agent |
| [langgraph-postmortem-team](langgraph-postmortem-team/) | Python · LangGraph | A planner loop in a single deep trace, with the graph view and cost per node |
| [mastra-utility-account-agent](mastra-utility-account-agent/) | TypeScript · Mastra (OTel) | Agent-loop trees with real `execute_tool` spans |
| [voltagent-bike-repair-desk](voltagent-bike-repair-desk/) | TypeScript · VoltAgent (OTel) | A `gen_ai.*` mapping that turns blank spans into priced llm spans |
| [beeai-recipe-substitution-agent](beeai-recipe-substitution-agent/) | TypeScript · BeeAI (OpenInference) | ReAct iterations, llm calls and tool runs, including a tool lookup that misses |
| [smolagents-brewery-batch-analyst](smolagents-brewery-batch-analyst/) | Python · smolagents (OpenInference) | The pandas code the agent wrote, and what happened when it ran |
| [temporal-py-grant-review](temporal-py-grant-review/) | Python · Temporal | One trace across two processes, with the failed attempt next to its retry |

### Retrieval

| Example | Stack | What to look at in Opik |
|---|---|---|
| [langgraph-boardgame-rules-rag](langgraph-boardgame-rules-rag/) | Python · LangChain + LangGraph | Retrieve/generate spans; an experiment pair scored for hallucination and context precision |
| [llamaindex-syllabus-pdf-qa](llamaindex-syllabus-pdf-qa/) | Python · LlamaIndex | Retrieval and synthesis spans over PDFs, a guardrail span, a policy test suite |
| [otel-node-aquarium-care-rag](otel-node-aquarium-care-rag/) | TypeScript · plain OpenTelemetry | A Node service with no Opik SDK, yet with prompt text, usage and cost on its spans |
| [ollama-ham-radio-rag](ollama-ham-radio-rag/) | Python · Ollama + LangChain | A fully local pipeline: zero cloud calls, still fully traced |

### Evaluation, prompts and quality gates

| Example | Stack | What to look at in Opik |
|---|---|---|
| [anthropic-ts-espresso-manual-qa](anthropic-ts-espresso-manual-qa/) | TypeScript · Anthropic SDK | A test suite whose plain-English assertions check every quoted line |
| [pydantic-ai-calendar-extraction](pydantic-ai-calendar-extraction/) | Python · Pydantic AI (OTel) | A suite that catches values the model invented, comparing a strict prompt with an eager one |
| [opik-ts-error-message-prompts](opik-ts-error-message-prompts/) | TypeScript · Opik SDK | Two prompt-library versions and a suite going 0/5 → 5/5 |
| [optimizer-plant-problem-classifier](optimizer-plant-problem-classifier/) | Python · Opik Agent Optimizer | A score curve across trials; the winning prompt saved to the library |
| [vercel-ai-sveltekit-stargazing-chat](vercel-ai-sveltekit-stargazing-chat/) | TypeScript · Vercel AI SDK + SvelteKit | Streaming spans, threads, and an online LLM-judge rule scoring live traffic |

### Tracing mechanics: cost, threads, attachments, manual spans

| Example | Stack | What to look at in Opik |
|---|---|---|
| [litellm-exhibit-labels](litellm-exhibit-labels/) | Python · LiteLLM | Same prompts on two providers, with cost and latency side by side |
| [langchain-fastapi-library-chat](langchain-fastapi-library-chat/) | Python · LangChain + FastAPI | Threads that read like clean chat transcripts |
| [openai-ts-storybook-illustrator](openai-ts-storybook-illustrator/) | TypeScript · OpenAI images | Generated PNGs attached to traces; a v1 → v2 prompt diff you can see |
| [opik-py-redaction-pipeline](opik-py-redaction-pipeline/) | Python · Opik SDK (manual) | Hand-built traces and spans, recorded usage, feedback scores, flush behaviour |

## Running one

You need an Opik to send traces to. The quickest is a local one:

```bash
git clone https://github.com/comet-ml/opik.git && cd opik && ./opik.sh   # UI at http://localhost:5173
```

Then:

1. Copy `.env.example` to `.env` at the repo root and add your `OPENAI_API_KEY` (plus `ANTHROPIC_API_KEY` for the
   two examples that use it). Every example finds this file by walking up from its own folder.
2. `cd` into an example and follow its README. Python examples use [uv](https://docs.astral.sh/uv/)
   (`uv run main.py` or a small CLI); TypeScript ones use `npm install && npm run demo`.
3. Open the Opik UI and pick the project with the same name as the folder.

Each run costs from a fraction of a cent up to about ten cents; the README of each example gives its own figure.
To use Opik Cloud instead of a local install, set `OPIK_URL_OVERRIDE` and `OPIK_API_KEY` as described in `.env.example`.

## Inside every folder

- `README.md`: the problem, what to open in Opik, numbers from a real run, things to try next, and a
  **Gotchas** section of symptoms we actually hit, each with its cause and fix.
- `.env.example`: only the variables that example reads.
- The app itself, with comments on every place it touches Opik.
- `data/` or `docs/`: a small fictional corpus, so nothing depends on outside APIs.
- `tests/`: offline tests that run in seconds with no keys and tracing switched off.

The git history is worth a look too. Many examples arrive as a short series of commits: first the app with no
tracing, then tracing, then the evaluation layer. Each diff is exactly the change you'd make to your own code.

## License

[Apache 2.0](LICENSE).

---

<sub>Inspired by Opik's examples and [documentation](https://www.comet.com/docs/opik/) · [Opik on GitHub](https://github.com/comet-ml/opik)</sub>
