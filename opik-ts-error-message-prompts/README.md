# opik-ts-error-message-prompts

*Raw stack traces in, friendly toast copy out: one prompt, two library versions, a suite that goes from 0% to 100%.*

![TypeScript](https://img.shields.io/badge/TypeScript-strict-3178C6?style=flat&logo=typescript&logoColor=white)
![Opik](https://img.shields.io/badge/opik-2.2.99-2f54eb?style=flat)
![Model](https://img.shields.io/badge/model-gpt--4o--mini-412991?style=flat)

Error copy is a prompt like any other, and it tends to live as a string literal that someone tweaks until the toast "sounds nicer". Then a user sees `10.4.2.17:5432` in a popup and nobody can say which wording shipped. Here the rewriting prompt lives in Opik's prompt library, every edit is an immutable version, and a judged test suite is run against each version so the edit's effect is a number.

## What you'll build

A small Node script for a fictional task tracker called Tallyboard. It takes five raw errors (a React `TypeError` with stack frames, a Postgres `ECONNREFUSED`, an HTTP 413, a validation failure, a 403 with user and workspace ids) and asks `gpt-4o-mini` to turn each into UI copy. The system prompt is the library prompt `error-to-ui-copy`:

- **v1** says "sound friendly and polite, keep the original details so support can still diagnose".
- **v2** adds rules: two sentences max, no codes, class names, paths or hostnames, give one next step, never blame the user.

A test suite with four plain-language assertions (matching v2's rules) is run once per version through `runTests`, so you get two experiments to compare.

## See it in Opik

Open the **opik-ts-error-message-prompts** project.

- **Prompt library**: `error-to-ui-copy` has exactly two versions, `v1` and `v2`, each with its change description. Open the version history and compare them to see the diff: v2 adds the bullet list of rules. Re-running the demo does not add `v3`.
- **Test suites / Experiments**: two runs, `error-to-ui-copy-v1` and `error-to-ui-copy-v2`, over the same five items (3 judged runs per item, an item passes with 2 of 3). In the verified run, v1 passed 0 of 5 items and v2 passed 5 of 5. v1's copy is polite but carries things like `10.4.2.17:5432` and `2021-03-09` straight through; v2's reads like "The due date you entered is in the past. Please choose a future date and try again." Each experiment is linked to the prompt version it tested.
- **Traces**: 31 traces. One is the demo rewrite, `rewrite-error-copy`, whose metadata includes the `opik_prompts` reference (name, version id, commit) of the prompt that ran. The other 30 are `evaluation_task` traces, one per judged run (2 versions x 5 items x 3 runs). Open a `rewrite-error-copy` trace to see a child span `rewrite-error` with the exact system prompt and raw error as input, the model, token usage and an estimated cost (about $0.00004 per rewrite).

## Run it yourself

1. Start Opik locally and note the API URL. Copy `.env.example` to `.env` and set `OPENAI_API_KEY` (a repo-root `.env` one level up also works).
2. `npm install`
3. `export OPIK_URL_OVERRIDE=http://localhost:5173/api/ OPIK_WORKSPACE=default` (skip for Opik Cloud, set `OPIK_API_KEY` instead).
4. `npm run demo` (about a minute, well under $0.10).
5. Offline tests: `OPIK_TRACK_DISABLE=true npm test`. They need no keys and no Opik; `OPIK_TRACK_DISABLE=true` makes `track()` a pass-through (the vitest config also sets it).

## Poke around

- Add a rule to `PROMPT_V2` in `src/prompts.ts` (for example "start with an emoji") and run again: you get a `v3`, and the diff view shows the added line.
- Drop the sentence cap from v2 and see which assertion starts failing in the per-item results.
- Add a sixth, nastier raw error to `src/errors.ts` (an SQL statement with a table name) and see whether v2 still holds.
- Open a trace's metadata and find which prompt version produced that copy.

## Gotchas we hit

**1. `npm install` fails with `ERESOLVE` on `opik-openai`.** Its peer dependency is `opik@^1.8.61` while the current SDK is `opik@2.2.99`. Add an override to `package.json`:
`"overrides": { "opik-openai": { "opik": "2.2.99" } }`.

**2. The prompt library grows `v3`, `v4`, ... on every run.** `createPrompt` is idempotent only against the latest version. Calling it with v1 text and then v2 text each run creates a new version every time (v1 differs from latest v2, then v2 differs from v1). `registerPrompts` in `src/suite.ts` reads `prompt.getVersions()` first and skips any text already present.

**3. Every model call is its own root trace named `rewrite-error`.** `trackOpenAI` does not read the context of `track()`. Pass the current span as the parent: `trackOpenAI(client, { client: opik, parent: getTrackContext()?.span })` (`getTrackContext` is exported by `opik`). Then the call nests under `rewrite-error-copy`.

**4. The OpenAI span is type `general`, not `llm`.** With `opik-openai@2.2.99` the span carries model, provider, token usage and `totalEstimatedCost`, but its type column says `general`. The judge's own calls (`model.generateText`) are the `llm` spans in this project. Nothing to fix; just don't filter on `llm` to find the rewrite calls.

**5. A wall of `AI SDK Warning: System messages in the prompt...` lines during the suite.** The LLM judge goes through the Vercel AI SDK, which warns once per call. It is harmless; filter with `grep -v "AI SDK Warning"`.

## How it's put together

- `src/prompts.ts`: project, prompt name, the two prompt versions, change descriptions, the four assertions.
- `src/errors.ts`: the five fictional raw errors.
- `src/rewrite.ts`: Opik client, OpenAI call wrapped with `trackOpenAI`, and the `track()`-wrapped `rewriteError` that fetches the prompt version from the library.
- `src/suite.ts`: dedupe-safe prompt registration, test suite creation, and `runTests` per version.
- `src/main.ts`: registers prompts, runs one traced rewrite, runs both versions, prints the comparison, flushes.
- `src/env.ts`: loads `.env`.
- `tests/app.test.ts`: offline tests for the prompts, the message layout, a traced function with tracking off, and prompt registration dedupe.

---

*built with Opik · inspired by Opik's examples and documentation*
