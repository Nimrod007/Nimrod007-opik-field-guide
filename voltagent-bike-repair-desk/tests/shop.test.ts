import { describe, it, expect, beforeAll } from "vitest";

// Tracing off: with no span processor registered, nothing is exported.
process.env.OTEL_SDK_DISABLED = "true";

import { lookupPartsImpl, quoteRepairImpl, bookSlotImpl, lookupParts, SLOTS } from "../src/shop.ts";

describe("shop tools", () => {
  it("finds parts by keyword", () => {
    expect(lookupPartsImpl("brake pads").map((p) => p.sku)).toContain("BRK-110");
  });

  it("quotes labor plus parts and flags out-of-stock SKUs", () => {
    const q = quoteRepairImpl("drivetrain replacement", ["CHN-212", "CAS-118"]);
    expect(q).toMatchObject({ labor_usd: 85, parts_usd: 96, total_usd: 181, out_of_stock: ["CAS-118"] });
  });

  it("rejects unknown jobs and SKUs", () => {
    expect(quoteRepairImpl("paint job", [])).toHaveProperty("error");
    expect(quoteRepairImpl("flat repair", ["NOPE"])).toHaveProperty("error");
  });

  it("books an open slot once, then refuses it", () => {
    expect(SLOTS["2026-11-03"]).toContain("10:00");
    expect(bookSlotImpl("Sam", "2026-11-03", "10:00", "flat repair")).toMatchObject({ booked: true });
    expect(bookSlotImpl("Lee", "2026-11-03", "10:00", "flat repair")).toMatchObject({ booked: false });
  });

  it("runs a registered VoltAgent tool with tracing disabled", async () => {
    const out = (await (lookupParts as any).execute({ query: "tube" })) as { matches: { sku: string }[] };
    expect(out.matches[0].sku).toBe("TUB-700");
  });
});

describe("GenAI attribute mapping", () => {
  let mapToGenAI: typeof import("../src/observability.ts").mapToGenAI;
  beforeAll(async () => {
    ({ mapToGenAI } = await import("../src/observability.ts"));
  });

  it("copies usage, model and provider onto llm spans so cost can be priced", () => {
    const a = mapToGenAI({
      "span.type": "llm", "llm.model": "gpt-4o-mini",
      "llm.usage.prompt_tokens": 10, "llm.usage.completion_tokens": 5, "llm.usage.total_tokens": 15,
    });
    expect(a).toMatchObject({
      "gen_ai.request.model": "gpt-4o-mini", "gen_ai.provider.name": "openai",
      "gen_ai.usage.prompt_tokens": 10, "gen_ai.usage.completion_tokens": 5, "gen_ai.usage.total_tokens": 15,
    });
  });

  it("moves tool arguments to gen_ai.tool.call.arguments", () => {
    const a = mapToGenAI({ "span.type": "tool", input: '{"query":"x"}', "tool.parameters": "{}" });
    expect(a["gen_ai.tool.call.arguments"]).toBe('{"query":"x"}');
    expect(a).not.toHaveProperty("input");
  });
});
