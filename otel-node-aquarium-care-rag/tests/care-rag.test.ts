import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { InMemorySpanExporter } from "@opentelemetry/sdk-trace-base";
import { chunkMarkdown } from "../src/chunk.js";
import { cosine, topK } from "../src/retrieve.js";
import { buildMessages, CareRag } from "../src/rag.js";
import { createApp } from "../src/server.js";
import { flushTelemetry, initTelemetry, shutdownTelemetry } from "../src/telemetry.js";

// Fake OpenAI client: embeddings are 2-d vectors keyed on a word, chat echoes a fixed answer.
function fakeClient() {
  const vec = (t: string) => (t.toLowerCase().includes("feed") ? [0, 1] : [1, 0]);
  return {
    embeddings: {
      create: async ({ input }: { input: string | string[] }) => ({
        data: (Array.isArray(input) ? input : [input]).map((t) => ({ embedding: vec(t) })),
        usage: { prompt_tokens: 7 },
      }),
    },
    chat: {
      completions: {
        create: async () => ({
          model: "gpt-4o-mini-2024-07-18",
          choices: [{ message: { content: "Twice a day." } }],
          usage: { prompt_tokens: 100, completion_tokens: 5 },
        }),
      },
    },
  } as never;
}

async function makeRag() {
  const rag = new CareRag(fakeClient());
  await rag.ingest(new URL("../docs", import.meta.url).pathname);
  return rag;
}

describe("retrieval", () => {
  it("chunks by section heading", () => {
    const chunks = chunkMarkdown("a.md", "# T\n## One\nfoo\n## Two\nbar\n");
    expect(chunks.map((c) => c.heading)).toEqual(["One", "Two"]);
    expect(chunks[1]!.text).toContain("bar");
  });
  it("ranks by cosine similarity", () => {
    expect(cosine([1, 0], [1, 0])).toBeCloseTo(1);
    const idx = [
      { id: "a", source: "a", heading: "A", text: "a", vector: [1, 0] },
      { id: "b", source: "b", heading: "B", text: "b", vector: [0, 1] },
    ];
    expect(topK([0, 1], idx, 1)[0]!.chunk.id).toBe("b");
  });
  it("puts excerpts and the question in the user message", () => {
    const msgs = buildMessages("How often?", [{ chunk: { id: "x", source: "f.md", heading: "H", text: "H\nTwice" }, score: 1 }]);
    expect(msgs[1]!.content).toContain("(f.md)");
    expect(msgs[1]!.content).toContain("Question: How often?");
  });
});

describe("http service", () => {
  it("rejects a missing question and answers a real one", async () => {
    const app = createApp(await makeRag());
    expect((await app.request("/ask", { method: "POST", body: "{}" })).status).toBe(400);
    const res = await app.request("/ask", { method: "POST", body: JSON.stringify({ question: "how to feed?" }) });
    expect(((await res.json()) as { answer: string }).answer).toBe("Twice a day.");
  });
});

describe("OTel spans", () => {
  let exporter: InMemorySpanExporter;
  beforeEach(() => {
    delete process.env.OTEL_SDK_DISABLED; // these tests exercise the SDK on purpose
    exporter = new InMemorySpanExporter(); // a shut-down exporter stays stopped, so use a fresh one per test
    initTelemetry(exporter);
  });
  afterEach(async () => {
    await shutdownTelemetry();
    delete process.env.OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT;
  });

  async function askAndCollect() {
    const app = createApp(await makeRag());
    exporter.reset();
    await app.request("/ask", { method: "POST", body: JSON.stringify({ question: "how to feed?" }) });
    await flushTelemetry(); // pushes the batch processor into the in-memory exporter
    return exporter.getFinishedSpans();
  }

  it("records usage and nests spans under the request, but no text by default", async () => {
    const spans = await askAndCollect();
    const chat = spans.find((s) => s.name === "chat gpt-4o-mini")!;
    expect(chat.attributes["gen_ai.usage.input_tokens"]).toBe(100);
    expect(chat.attributes["gen_ai.provider.name"]).toBe("openai");
    expect(chat.attributes["gen_ai.prompt"]).toBeUndefined();
    expect(chat.attributes["gen_ai.completion"]).toBeUndefined();
    const root = spans.find((s) => s.name === "POST /ask")!;
    expect(chat.parentSpanContext?.spanId).toBe(root.spanContext().spanId);
  });

  it("adds prompt and completion text when content capture is switched on", async () => {
    process.env.OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT = "true";
    const chat = (await askAndCollect()).find((s) => s.name === "chat gpt-4o-mini")!;
    expect(String(chat.attributes["gen_ai.prompt"])).toContain("Question: how to feed?");
    expect(JSON.parse(String(chat.attributes["gen_ai.completion"]))).toEqual({ role: "assistant", content: "Twice a day." });
  });
});

describe("tracing disabled", () => {
  it("still answers when OTEL_SDK_DISABLED=true (spans are no-ops)", async () => {
    process.env.OTEL_SDK_DISABLED = "true";
    try {
      expect((await (await makeRag()).answer("how to feed?")).answer).toBe("Twice a day.");
    } finally {
      delete process.env.OTEL_SDK_DISABLED;
    }
  });
});
