// Plays three scripted customer conversations through the intake assistant.
// Each becomes one trace in the Opik project "voltagent-bike-repair-desk".
import { config } from "dotenv";
import { fileURLToPath } from "node:url";

config({
  path: [fileURLToPath(new URL("../.env", import.meta.url)), fileURLToPath(new URL("../../.env", import.meta.url))],
  quiet: true,
});
delete process.env.OPENAI_BASE_URL; // use the public OpenAI API, not a local proxy

// VoltAgent puts the system prompt in the messages array, which makes the AI SDK
// warn on every call; this is VoltAgent's layout, so drop that one known line.
const realWarn = console.warn.bind(console);
console.warn = (...args: unknown[]) => {
  if (typeof args[0] === "string" && args[0].includes("System messages in the prompt")) return;
  realWarn(...args);
};

if (!process.env.OPENAI_API_KEY) {
  console.error("Missing OPENAI_API_KEY. Copy .env.example to .env and fill it in.");
  process.exit(1);
}

// Import after env is loaded: the exporter reads its settings at import time.
const { VoltAgent } = await import("@voltagent/core");
const { observability } = await import("./observability.ts");
const { intakeAssistant } = await import("./agent.ts");

// Registering the agent hands it the Opik-wired observability. No server option: this stays a script.
new VoltAgent({ agents: { intakeAssistant }, observability });

const CONVERSATIONS = [
  "My disc brakes squeal and feel weak. What do new pads cost, are they in stock, and what would a brake service come to?",
  "My 11-speed drivetrain is worn out. Quote me a drivetrain replacement with a new chain and cassette.",
  "Please book a gear tune-up for Priya Nair on 2026-11-02 at 13:00.",
];

for (const [i, text] of CONVERSATIONS.entries()) {
  console.log(`\n=== Customer ${i + 1} ===\nCustomer:  ${text}`);
  const result = await intakeAssistant.generateText(text);
  console.log(`Assistant: ${result.text}`);
}

// Shutdown flushes the batch span processor so the last spans reach Opik before exit.
await observability.shutdown();
console.log('\nDone. Open the "voltagent-bike-repair-desk" project in Opik.');
process.exit(0);
