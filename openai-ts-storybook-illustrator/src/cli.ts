// Storybook illustrator CLI: `npm run demo [-- --version v1|v2|both]`.
import path from "node:path";
import process from "node:process";
import OpenAI from "openai";
import { Opik } from "opik";
import { PAGES } from "./briefs/pages.js";
import { registerBriefs } from "./briefs/library.js";
import { illustratePage, openaiClientFor } from "./render/pipeline.js";

// A local dev proxy may set an OpenAI base URL; this example talks to the public API.
delete process.env.OPENAI_BASE_URL;

// Load the example's .env, then the repo-root one. Existing env vars win.
for (const f of [".env", "../.env"]) {
  try {
    process.loadEnvFile(path.resolve(f));
  } catch {
    /* no file: keys may come from the environment */
  }
}

export const PROJECT = "openai-ts-storybook-illustrator";
const OUT_DIR = "output";

export function parseVersions(argv: string[]): ("v1" | "v2")[] {
  const i = argv.indexOf("--version");
  const v = i >= 0 ? argv[i + 1] : "both";
  if (v === "v1" || v === "v2") return [v];
  if (v === "both") return ["v1", "v2"];
  throw new Error(`--version must be v1, v2 or both (got "${v}")`);
}

async function main() {
  if (!process.env.OPENAI_API_KEY) {
    console.error("OPENAI_API_KEY is not set. Add it to .env and re-run.");
    process.exit(1);
  }
  const versions = parseVersions(process.argv.slice(2));

  // Every trace, span and prompt below lands in this Opik project.
  const opik = new Opik({ projectName: PROJECT });
  const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
  try {
    const briefs = await registerBriefs(opik, PROJECT);
    for (const label of versions) {
      console.log(`\nIllustrating with brief ${label}:`);
      for (const page of PAGES) {
        const { file } = await illustratePage(opik, openaiClientFor(openai, opik), briefs[label], page, OUT_DIR);
        console.log(`  ${page.id} -> ${file}`);
      }
    }
  } finally {
    // flush sends batched traces/spans and uploads the PNG attachments before exit.
    await opik.flush();
  }
  console.log(`\nDone. Open project "${PROJECT}" in Opik.`);
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(import.meta.filename)) {
  main().catch((e) => {
    console.error("Run failed:", e);
    process.exit(1);
  });
}
