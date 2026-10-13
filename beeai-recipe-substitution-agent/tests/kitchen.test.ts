import { describe, expect, it } from "vitest";
import { convertUnits, pantryLookup, substitutionTable } from "../src/kitchen.ts";
import { pantryLookupTool, substitutionTableTool, unitConversionTool } from "../src/tools.ts";
import { startTracing, OPIK_PROJECT } from "../src/tracing.ts";

describe("kitchen logic", () => {
  it("looks up pantry stock, treating plurals and case alike", () => {
    expect(pantryLookup("Milk")).toMatchObject({ in_stock: true, amount: 500, unit: "ml" });
    expect(pantryLookup("eggs")).toMatchObject({ in_stock: false, amount: 0 });
    expect(pantryLookup("saffron")).toHaveProperty("error");
  });

  it("flags substitutes the pantry can cover", () => {
    const t = substitutionTable("buttermilk") as { options: { can_make_now: boolean }[] };
    expect(t.options.every((o) => o.can_make_now)).toBe(true);
    const butter = substitutionTable("unsalted butter") as { options: { substitute: string }[] };
    expect(butter.options[0].substitute).toBe("olive oil");
    expect(substitutionTable("unobtainium")).toHaveProperty("error");
  });

  it("converts units through ingredient density", () => {
    expect(convertUnits(2, "each", "g", "eggs")).toMatchObject({ amount: 100, unit: "g" });
    expect(convertUnits(1, "cup", "ml", "milk")).toMatchObject({ amount: 236.59 });
    expect(convertUnits(150, "g", "ml", "olive oil")).toMatchObject({ unit: "ml", amount: 164.84 });
    expect(convertUnits(1, "cup", "g", "dragonfruit")).toHaveProperty("error");
  });
});

describe("tools and tracing switch", () => {
  it("runs BeeAI tools with tracing disabled", async () => {
    const tracing = startTracing({ OTEL_SDK_DISABLED: "true" });
    expect(tracing.enabled).toBe(false);
    const out = await pantryLookupTool.run({ ingredient: "honey" });
    expect(JSON.parse(out.getTextContent())).toMatchObject({ in_stock: true, unit: "g" });
    const conv = await unitConversionTool.run({ amount: 1, from: "cup", to: "ml", ingredient: "water" });
    expect(JSON.parse(conv.getTextContent()).amount).toBeCloseTo(236.59);
    const sub = await substitutionTableTool.run({ ingredient: "cake flour" });
    expect(sub.getTextContent()).toContain("cornstarch");
    await tracing.shutdown();
  });

  it("targets the example's Opik project", () => {
    expect(OPIK_PROJECT).toBe("beeai-recipe-substitution-agent");
  });
});
