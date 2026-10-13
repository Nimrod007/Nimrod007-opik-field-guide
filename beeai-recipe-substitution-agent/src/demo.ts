// Plays the scripted requests in data/requests.json through the agent.
import { config } from "dotenv";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

// The example's own .env first, then the repo-root .env.
config({
  path: [fileURLToPath(new URL("../.env", import.meta.url)), fileURLToPath(new URL("../../.env", import.meta.url))],
  quiet: true,
});
if (!process.env.OPENAI_API_KEY) {
  console.error("Missing OPENAI_API_KEY. Copy .env.example to .env and fill it in.");
  process.exit(1);
}
// Some dev machines route OpenAI traffic through a proxy via this variable; use the public API.
delete process.env.OPENAI_BASE_URL;

const { findSubstitution } = await import("./agent.ts");

const requests: string[] = JSON.parse(
  readFileSync(fileURLToPath(new URL("../data/requests.json", import.meta.url)), "utf8"),
);

for (const [i, request] of requests.entries()) {
  console.log(`\n=== Request ${i + 1} ===\nCook: ${request}`);
  console.log(`Answer:\n${await findSubstitution(request)}`);
}
