import { Hono } from "hono";
import { SpanKind } from "@opentelemetry/api";
import type { CareRag } from "./rag.js";
import { captureContent, withSpan } from "./telemetry.js";

export function createApp(rag: Pick<CareRag, "answer">) {
  const app = new Hono();
  app.get("/health", (c) => c.json({ ok: true }));
  app.post("/ask", async (c) => {
    const body = await c.req.json().catch(() => null) as { question?: unknown } | null;
    const question = typeof body?.question === "string" ? body.question.trim() : "";
    if (!question) return c.json({ error: "question is required" }, 400);
    // Root span of the trace: one per HTTP request, so each question is one trace in Opik.
    // Retrieval and chat spans created inside rag.answer() nest under it.
    const result = await withSpan("POST /ask", { "http.request.method": "POST", "url.path": "/ask" }, async (span) => {
      if (captureContent()) span.setAttribute("input", JSON.stringify({ question }));
      const r = await rag.answer(question);
      if (captureContent()) span.setAttribute("output", JSON.stringify({ answer: r.answer, sources: r.sources }));
      return r;
    }, SpanKind.SERVER);
    return c.json(result);
  });
  return app;
}
