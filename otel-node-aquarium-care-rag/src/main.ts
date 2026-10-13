import "./config.js";
import { serve } from "@hono/node-server";
import OpenAI from "openai";
import { CareRag } from "./rag.js";
import { createApp } from "./server.js";

const rag = new CareRag(new OpenAI());
const n = await rag.ingest(new URL("../docs", import.meta.url).pathname);
console.log(`indexed ${n} chunks`);
const port = Number(process.env.PORT ?? 4290);
serve({ fetch: createApp(rag).fetch, port });
console.log(`listening on http://localhost:${port}`);
