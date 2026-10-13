// Plays scripted customer questions through the account agent. `npm run demo`.
import { config } from "dotenv";
import { fileURLToPath } from "node:url";

config({
  path: [
    fileURLToPath(new URL("../.env", import.meta.url)),
    fileURLToPath(new URL("../../.env", import.meta.url)),
  ],
  quiet: true,
});

if (!process.env.OPENAI_API_KEY) {
  console.error("Missing OPENAI_API_KEY. Copy .env.example to .env and fill it in.");
  process.exit(1);
}

// Import after env is loaded.
const { mastra, OPIK_PROJECT } = await import("./mastra.ts");
const { SCRIPT } = await import("./script.ts");

const agent = mastra.getAgent("accountAgent");
for (const [i, question] of SCRIPT.entries()) {
  console.log(`\n=== Question ${i + 1} ===\nCustomer: ${question}`);
  const result = await agent.generate(question, { maxSteps: 6 });
  console.log(`Agent:    ${result.text}`);
}

// Flush the OTel exporter: spans are batched, and without this the last trace can be lost on exit.
await mastra.shutdown();
console.log(`\nDone. Open the "${OPIK_PROJECT}" project in Opik to see the traces.`);
