import OpenAI from "openai";
import { Opik, getTrackContext, track } from "opik";
import { trackOpenAI } from "opik-openai";
import { MODEL, PROJECT_NAME, PROMPT_NAME } from "./prompts.js";

// The Opik client owns the prompt library calls and the final flush.
export const opik = new Opik({ projectName: PROJECT_NAME });

// Created lazily so importing this module (tests) needs no OPENAI_API_KEY.
let openaiClient: OpenAI | undefined;
export type Complete = (system: string, user: string) => Promise<string>;

const complete: Complete = async (system, user) => {
  // trackOpenAI wraps the client: each completion becomes an llm span with token usage and cost.
  // It does not read track()'s context by itself; without `parent` every call would land as its own
  // root trace. Passing the current span nests the llm span under "rewrite-error-copy".
  const openai = trackOpenAI((openaiClient ??= new OpenAI()), {
    client: opik,
    generationName: "rewrite-error",
    parent: getTrackContext()?.span,
  });
  const res = await openai.chat.completions.create({
    model: MODEL,
    temperature: 0,
    messages: [
      { role: "system", content: system },
      { role: "user", content: user },
    ],
  });
  return res.choices[0]?.message.content?.trim() ?? "";
};

/** Pure core: build the messages from a prompt text and call the model. Easy to stub in tests. */
export async function rewriteWith(promptText: string, rawError: string, call: Complete = complete) {
  return call(promptText, `Raw error:\n${rawError}`);
}

type PromptSource = (version?: string) => Promise<string>;

/** Build the traced rewrite function around any source of prompt text (the library in the app, a stub in tests). */
export function makeRewriter(source: PromptSource, call: Complete = complete) {
  // type "general": this wrapper is not itself the model call (the inner llm span is).
  // Inside track() the SDK also stamps the trace with the prompt version fetched via getPrompt.
  return track(
    { name: "rewrite-error-copy", projectName: PROJECT_NAME, type: "general" },
    async (rawError: string, version?: string): Promise<string> => rewriteWith(await source(version), rawError, call),
  );
}

/** Rewrite one raw error with a named prompt version (latest if omitted), fetched from the Opik prompt library at call time. */
export const rewriteError = makeRewriter(async (version) => {
  const prompt = await opik.getPrompt({ name: PROMPT_NAME, version, projectName: PROJECT_NAME });
  if (!prompt) throw new Error(`Prompt ${PROMPT_NAME} not found; run the demo to register it`);
  return prompt.prompt;
});
