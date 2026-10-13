import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import type OpenAI from "openai";
import { chunkMarkdown } from "./chunk.js";
import { CHAT_MODEL, EMBED_MODEL, TOP_K } from "./config.js";
import { topK, type Hit, type Indexed } from "./retrieve.js";

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

  async ingest(docsDir: string): Promise<number> {
    const chunks = readdirSync(docsDir)
      .filter((f) => f.endsWith(".md"))
      .sort()
      .flatMap((f) => chunkMarkdown(f, readFileSync(join(docsDir, f), "utf8")));
    const res = await this.client.embeddings.create({ model: EMBED_MODEL, input: chunks.map((c) => c.text) });
    this.index = chunks.map((c, i) => ({ ...c, vector: res.data[i]!.embedding }));
    return chunks.length;
  }

  async retrieve(question: string): Promise<Hit[]> {
    const res = await this.client.embeddings.create({ model: EMBED_MODEL, input: question });
    return topK(res.data[0]!.embedding, this.index, TOP_K);
  }

  async answer(question: string): Promise<Answer> {
    const hits = await this.retrieve(question);
    const res = await this.client.chat.completions.create({
      model: CHAT_MODEL,
      temperature: 0,
      messages: buildMessages(question, hits),
    });
    return {
      answer: res.choices[0]?.message.content ?? "",
      sources: hits.map((h) => `${h.chunk.source} > ${h.chunk.heading}`),
    };
  }
}
