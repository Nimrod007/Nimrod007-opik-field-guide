import type { Chunk } from "./chunk.js";

export interface Indexed extends Chunk {
  vector: number[];
}
export interface Hit {
  chunk: Chunk;
  score: number;
}

export function cosine(a: number[], b: number[]): number {
  let dot = 0, na = 0, nb = 0;
  for (let i = 0; i < a.length; i++) {
    const x = a[i] ?? 0, y = b[i] ?? 0;
    dot += x * y; na += x * x; nb += y * y;
  }
  return na && nb ? dot / Math.sqrt(na * nb) : 0;
}

export function topK(query: number[], index: Indexed[], k: number): Hit[] {
  return index
    .map((c) => ({ chunk: { id: c.id, source: c.source, heading: c.heading, text: c.text }, score: cosine(query, c.vector) }))
    .sort((a, b) => b.score - a.score)
    .slice(0, k);
}
