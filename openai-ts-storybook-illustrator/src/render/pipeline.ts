import fs from "node:fs";
import path from "node:path";
import OpenAI from "openai";
import type { Opik, Prompt } from "opik";
import { HERO, type StoryPage } from "../briefs/pages.js";
import { PROMPT_NAME } from "../briefs/templates.js";
import { imageTraceOutput } from "../attach/image.js";
import { generateImage, IMAGE_SIZE, IMAGE_MODEL, trackedClient, type ImageClient } from "./openai.js";

export function outputFile(dir: string, version: string, page: StoryPage): string {
  return path.join(dir, `${version}-${page.id}.png`);
}

// Fill the managed brief with this page's variables.
export function renderBrief(prompt: Pick<Prompt, "format">, page: StoryPage): string {
  return prompt.format({ ...HERO, ...page });
}

export interface RenderedPage {
  file: string;
  traceId: string;
}

// `clientFor` receives the page trace so the real run can wrap OpenAI with trackOpenAI
// (child span under that trace); tests pass a stub instead.
export async function illustratePage(
  opik: Opik,
  clientFor: (trace: unknown) => ImageClient,
  prompt: Prompt,
  page: StoryPage,
  outDir: string,
): Promise<RenderedPage> {
  const brief = renderBrief(prompt, page);
  const version = prompt.version ?? "unknown";

  // One trace per page illustration. Metadata carries the prompt name/version/id so
  // each picture in Opik says which brief produced it; tags allow filtering by version.
  const trace = opik.trace({
    name: "illustrate-page",
    input: { page: page.id, title: page.title, brief },
    tags: [version, page.id],
    metadata: { prompt_name: PROMPT_NAME, prompt_version: version, prompt_id: prompt.id },
  });
  try {
    const b64 = await generateImage(clientFor(trace), brief);
    const file = outputFile(outDir, version, page);
    fs.mkdirSync(outDir, { recursive: true });
    fs.writeFileSync(file, Buffer.from(b64, "base64"));
    // Output carrying the base64 image: Opik extracts it as a PNG attachment on this trace.
    trace.update({ output: imageTraceOutput(b64, IMAGE_MODEL, IMAGE_SIZE) });
    return { file, traceId: trace.data.id };
  } finally {
    trace.end();
  }
}

export function openaiClientFor(openai: OpenAI, opik: Opik) {
  return (trace: unknown) => trackedClient(openai, opik, trace);
}
