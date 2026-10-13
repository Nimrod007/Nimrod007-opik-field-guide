import { describe, expect, it } from "vitest";
import type Anthropic from "@anthropic-ai/sdk";
import {
  answerQuestion,
  extractQuotes,
  MANUAL,
  SYSTEM_PROMPT,
  unverifiedQuotes,
  type Messages,
} from "../src/qa.js";
import { ITEM_ASSERTIONS, QUESTIONS, UNANSWERABLE } from "../src/questions.js";
import { traceMessages } from "../src/tracing.js";

const fakeMessage = (text: string): Anthropic.Message =>
  ({
    id: "msg_1",
    type: "message",
    role: "assistant",
    model: "claude-haiku-4-5-20251001",
    stop_reason: "end_turn",
    stop_sequence: null,
    content: [{ type: "text", text, citations: null }],
    usage: { input_tokens: 10, output_tokens: 5 },
  }) as unknown as Anthropic.Message;

const stub = (text: string): Messages => ({ create: async () => fakeMessage(text) });

describe("quote helpers", () => {
  it("extracts every quote, trimmed", () => {
    expect(extractQuotes("a <quote> one </quote> b <quote>two\nlines</quote>")).toEqual([
      "one",
      "two\nlines",
    ]);
  });

  it("accepts verbatim quotes and flags paraphrases", () => {
    const real = "Do not use vinegar; it damages the boiler seals and voids the warranty.";
    const answer = `<quote>${real}</quote> <quote>Vinegar is bad for the seals.</quote>`;
    expect(unverifiedQuotes(answer)).toEqual(["Vinegar is bad for the seals."]);
  });
});

describe("prompt and data", () => {
  it("embeds the whole manual in the system prompt", () => {
    expect(SYSTEM_PROMPT).toContain(MANUAL);
    expect(SYSTEM_PROMPT).toContain("<quote>");
  });

  it("only pins item assertions to known questions", () => {
    for (const q of Object.keys(ITEM_ASSERTIONS)) {
      expect([...QUESTIONS, UNANSWERABLE]).toContain(q);
    }
  });
});

// These run with OPIK_TRACK_DISABLE=true: track() becomes a pass-through.
describe("traced functions with tracking disabled", () => {
  it("answerQuestion returns the model text", async () => {
    await expect(answerQuestion("q?", stub("hello <quote>x</quote>"))).resolves.toBe(
      "hello <quote>x</quote>",
    );
  });

  it("traceMessages still returns the underlying message", async () => {
    const traced = traceMessages(stub("hi"));
    const message = await traced.create({ model: "m", max_tokens: 1, messages: [] });
    expect(message.usage.input_tokens).toBe(10);
  });
});
