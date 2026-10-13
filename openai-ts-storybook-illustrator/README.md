# openai-ts-storybook-illustrator

*Same fox, two briefs: watch a children's book page change when the prompt gets a v2, with every picture attached to its trace.*

![Node](https://img.shields.io/badge/node-20.12%2B-5FA04E?style=flat&logo=node.js&logoColor=white)
![OpenAI SDK](https://img.shields.io/badge/openai-6.x-412991?style=flat&logo=openai&logoColor=white)
![Opik TS SDK](https://img.shields.io/badge/opik-2.2.99-2f54eb?style=flat)

A picture book lives or dies on consistency: the fox on page 2 has to be the fox from page 1. Image models don't remember anything between calls, so consistency comes from the brief, and briefs get edited. A few weeks in, nobody can say which wording produced the page that was approved, and the PNG itself tells you nothing about the prompt behind it.

## What you'll build

A small CLI illustrator for "Pip and the Lantern Moth", a story that does not exist. The illustration brief is a Mustache template stored in the Opik prompt library as `storybook-illustration-brief`, registered twice: v1 is a bare description (character, scene, mood), v2 adds a pinned character look, a watercolor house style, a no-lettering rule and reserved space for page text. The CLI renders each version for two story pages with `gpt-image-1` (lowest quality, 1024x1024, so four images, a few cents). Every page becomes one Opik trace carrying the prompt version, and the generated PNG is attached to that trace.

The code is split by job: `src/briefs/` (pages, templates, library registration), `src/render/` (OpenAI call and the per-page trace), `src/attach/` (turning an image into a trace attachment), and `src/cli.ts`.

## See it in Opik

Open the **openai-ts-storybook-illustrator** project. The Traces tab holds four `illustrate-page` traces, tagged `v1` or `v2` plus the page id, each with `prompt_name`, `prompt_version` and `prompt_id` in its metadata. Each trace has one child span, `images.generate`, with the rendered brief as input. In our verified run that span was typed `general`, with usage of 63 to 167 prompt tokens and 272 image output tokens, and an estimated cost of roughly $0.0003 (v1) to $0.0008 (v2) per image. Open any trace and the Attachments tab shows a 1.5 to 2.2 MB `output-attachment-...png`: the actual illustration, rendered inline.

Then open **Prompts** in the same project and pick `storybook-illustration-brief`. It has two versions, and the diff view shows exactly what v2 added. Put the v1 and v2 attachments next to each other and the difference is concrete: in our run the v1 pages were two different art styles (a dark oil-painting fox, then a pencil-and-crayon one) with no scarf, while both v2 pages were soft watercolor with Pip's green scarf, a cream chest and empty sky above him. Your images will differ run to run, which is the point: the trace tells you which brief produced which picture.

## Run it yourself

1. `cp .env.example .env` and add `OPENAI_API_KEY` (or rely on a repo-root `.env`). For a local Opik keep `OPIK_URL_OVERRIDE=http://localhost:5173/api/` and `OPIK_WORKSPACE=default`; for Opik Cloud use your URL, workspace and `OPIK_API_KEY`.
2. `npm install`
3. `npm run demo` (about 50 seconds; add `-- --version v2` to render only one brief version)
4. Open the project in Opik as described above. The PNGs are also written to `output/` (git-ignored, regenerated every run).

## Poke around

- Add a v3 to `BRIEF_VERSIONS` in `src/briefs/templates.ts` (say, "night scene, no moon") and re-run. Only the new version is created; traces get `prompt_version: v3`.
- Add a third page in `src/briefs/pages.ts` and watch whether Pip's scarf survives. Keep the cost in mind: each page is one image per version.
- Open an `images.generate` span and read the usage: image output is billed in tokens, and the span records them per generation.
- Run `npm run demo -- --version v1` twice and compare the attachments. Same brief, different foxes.

## Gotchas we hit

**Where the prompt lands.** On this Opik version prompts are scoped to a project. Symptom: the prompt is not under your project's Prompts tab, or a second copy of it appears elsewhere. Cause: `createPrompt` and `getPrompt` fall back to the client's default scope when no project is given. Fix: pass `projectName` to both, as `registerBriefs` does.

**Re-runs minting a v3.** Symptom: running the demo twice produces extra prompt versions. Cause: the TypeScript `createPrompt` only compares against the latest version, so re-creating v1 after v2 exists is treated as a change. Fix: list existing versions with `getVersions()` and create only the templates missing from the library (`missingBriefs` in `src/briefs/library.ts`).

**No picture on the trace.** Symptom: the trace shows only text. Cause: the image only becomes an attachment if the logged output carries it as a base64 `data:` URI above the extraction threshold (`OPIK_MIN_BASE64_EMBEDDED_ATTACHMENT_SIZE`, 256,000 characters by default). Fix: log `{ image: "data:image/png;base64,..." }` as the trace output, as `src/attach/image.ts` does. A 1024x1024 low-quality `gpt-image-1` PNG is well over the threshold.

**SDK typing and versions.** `opik-openai` needs `openai@^6`, `Trace` exposes `.data.id` rather than `.id`, and the npm `overrides` block in `package.json` keeps `opik-openai` on the same `opik` copy as the app.

## How it's put together

- `src/cli.ts`: entry point, `--version v1|v2|both`, creates the Opik client and flushes at the end.
- `src/briefs/pages.ts`: the fictional hero and the two story pages.
- `src/briefs/templates.ts`: the v1 and v2 brief templates and their change notes.
- `src/briefs/library.ts`: registers missing versions in the prompt library, prints the v1 to v2 diff.
- `src/render/openai.ts`: `gpt-image-1` call, wrapped with `trackOpenAI`.
- `src/render/pipeline.ts`: one trace per page, metadata, PNG written to `output/`.
- `src/attach/image.ts`: builds the base64 data-URI trace output.
- `tests/units.test.ts`: offline vitest checks (stubbed client). Run `OPIK_TRACK_DISABLE=true npm test`; the tracking switch is the SDK's `OPIK_TRACK_DISABLE` env var.

*built with Opik · inspired by Opik's examples and documentation*
