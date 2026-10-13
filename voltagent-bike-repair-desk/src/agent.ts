import { Agent } from "@voltagent/core";
import { lookupParts, quoteRepair, bookSlot } from "./shop.ts";

export const MODEL = "gpt-4o-mini";

export const intakeAssistant = new Agent({
  name: "repair-intake-assistant",
  // VoltAgent's model router resolves this to the AI SDK OpenAI provider.
  model: `openai/${MODEL}`,
  instructions:
    "You are the repair intake assistant at Spoke & Sprocket Cycle Works, a bike shop. " +
    "Use lookup_parts before talking about parts or stock, quote_repair before stating any price, " +
    "and book_slot only when the customer clearly asks to book a specific date and time. " +
    "Never invent prices, stock or slots. If a part is out of stock, say so. Reply in 2-4 friendly sentences.",
  tools: [lookupParts, quoteRepair, bookSlot],
});
