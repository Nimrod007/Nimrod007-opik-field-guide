// SvelteKit imports this once when the server starts, so telemetry is registered before
// the first request. (The hook module itself has nothing else to do.)
import { config } from "dotenv";
import path from "node:path";
import { setupTelemetry } from "./lib/telemetry";

// Shared secrets live in a .env above this folder; dotenv never overrides variables already set.
config({ path: path.resolve(process.cwd(), "../.env"), quiet: true });
setupTelemetry();
