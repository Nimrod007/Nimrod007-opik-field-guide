import "./config.js";
import { serve } from "@hono/node-server";
import OpenAI from "openai";
import { CareRag } from "./rag.js";
import { createApp } from "./server.js";

const QUESTIONS = [
  "What temperature should I keep neon tetras at?",
  "Can I keep a betta with tiger barbs?",
  "My fish is floating sideways and can't stay level. What should I do?",
  "Can my fish go a week without food while I'm on holiday?",
  "What is the best brand of aquarium heater to buy?", // not in the guide: should say it doesn't know
];

const rag = new CareRag(new OpenAI());
await rag.ingest(new URL("../docs", import.meta.url).pathname);
const server = serve({ fetch: createApp(rag).fetch, port: Number(process.env.PORT ?? 4290) });
const base = `http://localhost:${process.env.PORT ?? 4290}`;

for (const question of QUESTIONS) {
  const res = await fetch(`${base}/ask`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ question }),
  });
  const body = (await res.json()) as { answer: string; sources: string[] };
  console.log(`\nQ: ${question}\nA: ${body.answer}\n   sources: ${body.sources.join(" | ")}`);
}
server.close();
