import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import Anthropic from "@anthropic-ai/sdk";

export const MODEL = "claude-haiku-4-5-20251001";

export const MANUAL = readFileSync(
  fileURLToPath(new URL("../docs/manual.md", import.meta.url)),
  "utf8",
);

export const SYSTEM_PROMPT = `You answer questions about the Brasa Lumina 7 espresso machine owner's manual, reproduced in full below.

Rules:
- Answer only from the manual. If the manual does not cover the question, say so plainly instead of guessing.
- Every factual claim in your answer must be backed by a citation: a verbatim excerpt from the manual wrapped in <quote>...</quote> tags, copied character-for-character.
- Keep answers short: the answer first, then the supporting quote(s).

<manual>
${MANUAL}
</manual>`;

// Minimal client surface the app needs; tests stub it.
export interface Messages {
  create(params: Anthropic.MessageCreateParamsNonStreaming): Promise<Anthropic.Message>;
}

// ANTHROPIC_BASE_URL may point at a dev proxy; this example talks to the real API.
export const anthropic = new Anthropic({ baseURL: "https://api.anthropic.com" });

export function extractText(message: Anthropic.Message): string {
  return message.content
    .flatMap((block) => (block.type === "text" ? [block.text] : []))
    .join("");
}

/** Pull every <quote>...</quote> excerpt out of an answer. */
export function extractQuotes(answer: string): string[] {
  return [...answer.matchAll(/<quote>([\s\S]*?)<\/quote>/g)].map((m) => m[1]!.trim());
}

/** Deterministic check: is every quote a verbatim substring of the manual? */
export function unverifiedQuotes(answer: string, manual: string = MANUAL): string[] {
  return extractQuotes(answer).filter((q) => !manual.includes(q));
}

export async function answerQuestion(
  question: string,
  messages: Messages = anthropic.messages,
): Promise<string> {
  const response = await messages.create({
    model: MODEL,
    max_tokens: 1024,
    system: SYSTEM_PROMPT,
    messages: [{ role: "user", content: question }],
  });
  return extractText(response);
}
