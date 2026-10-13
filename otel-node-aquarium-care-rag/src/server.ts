import { Hono } from "hono";
import type { CareRag } from "./rag.js";

export function createApp(rag: Pick<CareRag, "answer">) {
  const app = new Hono();
  app.get("/health", (c) => c.json({ ok: true }));
  app.post("/ask", async (c) => {
    const body = await c.req.json().catch(() => null) as { question?: unknown } | null;
    const question = typeof body?.question === "string" ? body.question.trim() : "";
    if (!question) return c.json({ error: "question is required" }, 400);
    return c.json(await rag.answer(question));
  });
  return app;
}
