// The three BeeAI tools the agent can call. Each wraps a pure function from kitchen.ts.
import { DynamicTool, JSONToolOutput } from "beeai-framework/tools/base";
import { z } from "zod";
import { pantryLookup, substitutionTable, convertUnits, VOLUME_UNITS } from "./kitchen.ts";

export const pantryLookupTool = new DynamicTool({
  name: "pantry_lookup",
  description: "Check how much of one ingredient is in the household pantry. Returns in_stock, amount and unit.",
  inputSchema: z.object({ ingredient: z.string().describe("Ingredient name, e.g. 'milk'.") }),
  async handler(input) {
    return new JSONToolOutput(pantryLookup(input.ingredient));
  },
});

export const substitutionTableTool = new DynamicTool({
  name: "substitution_table",
  description:
    "Look up known substitutes for a missing ingredient. Each option has a ratio, the pantry items it needs, and can_make_now (true when the pantry covers them).",
  inputSchema: z.object({ ingredient: z.string().describe("The missing ingredient, e.g. 'buttermilk' or 'egg'.") }),
  async handler(input) {
    return new JSONToolOutput(substitutionTable(input.ingredient));
  },
});

export const unitConversionTool = new DynamicTool({
  name: "unit_conversion",
  description:
    `Convert an amount of an ingredient between units (${VOLUME_UNITS.join(", ")}). Uses ingredient densities, so grams <-> cups/ml works for known ingredients.`,
  inputSchema: z.object({
    amount: z.number(),
    from: z.enum(VOLUME_UNITS),
    to: z.enum(VOLUME_UNITS),
    ingredient: z.string().describe("Ingredient being converted, e.g. 'olive oil'."),
  }),
  async handler(input) {
    return new JSONToolOutput(convertUnits(input.amount, input.from, input.to, input.ingredient));
  },
});

export const kitchenTools = [pantryLookupTool, substitutionTableTool, unitConversionTool];
