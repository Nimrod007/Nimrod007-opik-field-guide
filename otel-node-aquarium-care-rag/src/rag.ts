import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import type OpenAI from "openai";
import { chunkMarkdown } from "./chunk.js";
import { CHAT_MODEL, EMBED_MODEL, TOP_K } from "./config.js";
import { topK, type Hit, type Indexed } from "./retrieve.js";
import { captureContent, withSpan } from "./telemetry.js";

export const SYSTEM_PROMPT =
  "You are the care-desk assistant for Brindle Reef Aquatics. Answer using ONLY the care-guide excerpts provided. " +
  "If the excerpts do not contain the answer, say you don't know and suggest asking a vet or the shop. Be brief and practical.";

export function buildMessages(question: string, hits: Hit[]) {
  const context = hits.map((h, i) => `[${i + 1}] (${h.chunk.source}) ${h.chunk.text}`).join("\n\n");
  return [
    { role: "system" as const, content: SYSTEM_PROMPT },
    { role: "user" as const, content: `Care-guide excerpts:\n${context}\n\nQuestion: ${question}` },
  ];
}

export interface Answer {
  answer: string;
  sources: string[];
}

export class CareRag {
  private index: Indexed[] = [];
  constructor(private client: OpenAI) {}

  /** Embed texts. Each call is its own span so embedding tokens show up in Opik next to the chat tokens. */
  private async embed(input: string | string[]): Promise<number[][]> {
    // An "embeddings" span: gen_ai.* attributes carry model, provider and token usage.
    return withSpan(`embeddings ${EMBED_MODEL}`, { ...genAiBase("embeddings", EMBED_MODEL) }, async (span) => {
      if (captureContent()) span.setAttribute("input", JSON.stringify({ input: Array.isArray(input) ? `${input.length} chunks` : input }));
      const res = await this.client.embeddings.create({ model: EMBED_MODEL, input });
      span.setAttribute("gen_ai.usage.input_tokens", res.usage.prompt_tokens);
      return res.data.map((d) => d.embedding);
    });
  }

  async ingest(docsDir: string): Promise<number> {
    const chunks = readdirSync(docsDir)
      .filter((f) => f.endsWith(".md"))
      .sort()
      .flatMap((f) => chunkMarkdown(f, readFileSync(join(docsDir, f), "utf8")));
    const vectors = await this.embed(chunks.map((c) => c.text));
    this.index = chunks.map((c, i) => ({ ...c, vector: vectors[i]! }));
    return chunks.length;
  }

  async retrieve(question: string): Promise<Hit[]> {
    // A tool-style span around the vector search, with the question in and the chosen chunks out.
    return withSpan("retrieve_care_guide", {}, async (span) => {
      const [vec] = await this.embed(question);
      const hits = topK(vec!, this.index, TOP_K);
      // `input` / `output` attributes become the span's Input and Output panels in Opik.
      span.setAttribute("input", JSON.stringify({ question, top_k: TOP_K }));
      span.setAttribute("output", JSON.stringify({ hits: hits.map((h) => ({ source: h.chunk.source, heading: h.chunk.heading, score: +h.score.toFixed(3) })) }));
      return hits;
    });
  }

  async answer(question: string): Promise<Answer> {
    const hits = await this.retrieve(question);
    const messages = buildMessages(question, hits);
    // The chat span is what Opik shows as an llm span: model, provider, token usage and (opt-in) the messages.
    return withSpan(`chat ${CHAT_MODEL}`, { ...genAiBase("chat", CHAT_MODEL), "gen_ai.request.temperature": 0 }, async (span) => {
      if (captureContent()) {
        // Opik reads gen_ai.prompt / gen_ai.completion as the span's input / output (JSON strings).
        span.setAttribute("gen_ai.prompt", JSON.stringify({ messages }));
      }
      const res = await this.client.chat.completions.create({ model: CHAT_MODEL, temperature: 0, messages });
      const answer = res.choices[0]?.message.content ?? "";
      span.setAttributes({
        "gen_ai.response.model": res.model,
        "gen_ai.usage.input_tokens": res.usage?.prompt_tokens ?? 0,
        "gen_ai.usage.output_tokens": res.usage?.completion_tokens ?? 0,
      });
      if (captureContent()) {
        span.setAttribute("gen_ai.completion", JSON.stringify({ role: "assistant", content: answer }));
      }
      return { answer, sources: hits.map((h) => `${h.chunk.source} > ${h.chunk.heading}`) };
    });
  }
}

function genAiBase(operation: string, model: string) {
  return {
    "gen_ai.operation.name": operation,
    "gen_ai.system": "openai",
    "gen_ai.provider.name": "openai",
    "gen_ai.request.model": model,
  };
}
