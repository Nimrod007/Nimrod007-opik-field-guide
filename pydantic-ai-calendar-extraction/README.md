# pydantic-ai-calendar-extraction

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![Pydantic AI](https://img.shields.io/badge/pydantic--ai-2.x-E92063?style=flat)
![Opik](https://img.shields.io/badge/Opik-2.2%2B-2f54eb?style=flat)

*A calendar-event extractor whose test suite knows the difference between "read from the email" and "made up to fill the form".*

Ask a model to turn "lunch this coming Friday at noon, the usual spot" into a calendar event and it will happily hand you a start time, an end time, a timezone and a location. Only two of those were in the email. The event looks complete, so nobody notices the invented end time until someone shows up at the wrong hour. This project makes that failure visible: a Pydantic AI agent extracts typed `CalendarEvent`s from messy scheduling emails, every call is traced into Opik over OpenTelemetry, and an Opik test suite grades each extraction against plain-language assertions, so an invented value turns into a red row.

## What you'll build

- A `calendar_extraction` package with one job per module: `schema.py` (the `CalendarEvent` model and the email corpus loader), `agent.py` (the Pydantic AI agent and two system prompts), `tracing.py` (the Opik wiring), `suite.py` (the test suite), `grounding.py` (an offline invented-value check) and `cli.py` (the `calendar-extraction` command).
- Six fictional emails in `data/emails.json`, each with a sent date and its own assertions: a clean meeting invite, a lunch with no end time, a five-minute call, a webinar whose end time must be derived from "runs 45 minutes", a forwarded "we moved it to Friday" thread, and a "let's get coffee sometime" note that contains no event at all.
- Two prompts for the same agent. `strict` says "leave it null if it isn't stated". `eager` says "calendars need complete entries, guess the gaps". Running the suite with each gives you a before/after you can compare in Opik.

## See it in Opik

Run the suite for both prompts, then open the **pydantic-ai-calendar-extraction** project.

- **Traces tab.** One run of the suite produces 18 traces per prompt (6 emails, 3 runs each), so 36 in total. Each trace is named `evaluation_task` and contains the whole path of one email: `extract_event` (your function), `invoke_agent agent` (Pydantic AI), `chat gpt-4o-mini` (an `llm` span with prompt and completion token counts and an estimated cost), then the judge's own spans (`llm_judge`, `completion`). In the run recorded for this README the 36 traces held 76 `llm` spans, 71,037 tokens and about $0.035 of estimated cost, and no span had a null cost. A handful of traces show two `chat gpt-4o-mini` spans, meaning the agent made a second model call for that email, which is easy to miss without the trace. Running `calendar-extraction extract` instead gives a trace named `extract_event` with just the agent spans under it.
- **Experiments.** Open the suite's experiments, `calendar-strict-prompt-gpt-4o-mini` and `calendar-eager-prompt-gpt-4o-mini`, and compare them. In our run `strict` passed 5 of 6 emails and `eager` passed 3 of 6. Under `eager`, `lunch-friday` failed 0/3 because the end time came back as 13:00 although the email never says when lunch ends; `quick-call` failed 0/3 because the agent invented an end time (09:05), a timezone and a "Phone" location; and `coffee-someday` failed 0/3 because the agent produced a concrete date, times and a place for an email that makes no plan. Those are exactly the invented values the suite exists to catch.
- **Strict is not perfect.** Even `strict` lost `roadmap-sync` 0/3: the agent never lists Ines Duarte, the sender, among the attendees, while the item's assertion expects her. And `cold-chain-webinar` passed only 2 of 3 runs, because one run answered 17:00 for a webinar that starts at 16:00 and "runs 45 minutes". Re-run it and the exact picture will shift a little, since both the extractor and the judge are language models.
- **Test Suites tab.** The `pydantic-ai-calendar-extraction` suite holds six items, four global assertions that apply to every email, and an execution policy of three runs per item with two required to pass.

## Run it yourself

1. Install [uv](https://docs.astral.sh/uv/) and start an Opik instance. The defaults assume a local one at `http://localhost:5173` and workspace `default`.
2. `cp .env.example .env` and put your `OPENAI_API_KEY` in it (or keep it in a `.env` one directory up).
3. `uv sync`
4. See one extraction per email, with an offline warning for values the email cannot support: `uv run calendar-extraction extract`
5. Run the suite with the careful prompt: `uv run calendar-extraction suite --prompt strict`
6. Run it with the eager prompt and compare the two experiments in Opik: `uv run calendar-extraction suite --prompt eager`
7. Run the offline tests (no keys, no Opik): `OPIK_TRACK_DISABLE=true uv run pytest`

Each suite run takes roughly half a minute. The OTLP endpoint and workspace can be overridden with `OTEL_EXPORTER_OTLP_ENDPOINT` and `OPIK_WORKSPACE`; for Opik Cloud, use `https://www.comet.com/opik/api/v1/private/otel` and add `Authorization=<your key>` to `OTEL_EXPORTER_OTLP_HEADERS`.

## Poke around

- Edit an email in `data/emails.json` to remove the weekday, and see how the date assertions behave. Items are deduplicated by content, so an edited email becomes a new item next to the old one.
- Run `uv run calendar-extraction suite --model gpt-4.1-mini` and compare its pass rate against `gpt-4o-mini` on the same suite; each run is a new experiment.
- Change `EXECUTION_POLICY` in `suite.py` to `runs_per_item: 1` and rerun a few times. Items near the edge (`quick-call`, `cold-chain-webinar`) flip between runs; three-runs-two-pass is what steadies them.
- Add your own worst real email with two or three assertions about what must be null, and watch whether the agent respects them.

## Gotchas we hit

**`TypeError: DatasetItem() got multiple values for keyword argument 'id'` when inserting suite items.** The item's `data` dictionary had a key named `id`, which collides with the dataset item's own id. Name it something else, as `suite.py` does: `{"email_id": e.id, "sent": ..., "text": ...}`.

**Items fail for "not stated" nulls, or the judge contradicts itself on the same output.** Our first global assertion read "no value is invented", and the judge failed events for having a null date or an empty attendee list. The first judge run also failed `quick-call` while its own explanation said the values were supported. Say explicitly that null is acceptable ("a null value, or an empty attendees list, is always acceptable"), use a judge model (`model="gpt-4.1-mini"` in `run_tests`) that is not the extractor, and give the suite an execution policy such as `{"runs_per_item": 3, "pass_threshold": 2}`.

**The terminal fills with span trees, or a startup banner, on every run.** `logfire.configure` prints spans to the console by default; pass `console=False`. Set `PYDANTIC_AI_NO_BANNER=1` to silence the Pydantic AI banner.

## How it's put together

- `calendar_extraction/schema.py` defines `CalendarEvent`, the `Email` record, the loader for `data/emails.json` and the prompt text that includes the sent date.
- `calendar_extraction/agent.py` builds the Pydantic AI agent (`strict` and `eager` prompts) and the `@opik.track` function `extract_event`.
- `calendar_extraction/tracing.py` points logfire's OpenTelemetry export at Opik's OTLP endpoint and attaches `OpikSpanProcessor`, so Pydantic AI spans nest inside `extract_event`.
- `calendar_extraction/suite.py` creates the test suite, pushes its assertions and execution policy, and calls `opik.run_tests`.
- `calendar_extraction/grounding.py` is an offline check that flags a URL, place or attendee the email never mentions.
- `calendar_extraction/cli.py` is the `calendar-extraction extract` and `suite` command line.
- `data/emails.json` is the fictional corpus with per-email assertions.
- `tests/test_extraction.py` has six offline tests: corpus loading, prompt rendering, suite item shape, the grounding check on bad and good events, and a traced `extract_event` call on a stub model with tracking disabled.

---

*built with Opik · inspired by Opik's examples and documentation*
