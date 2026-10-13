import { config } from "dotenv";
import { fileURLToPath } from "node:url";

// Keys come from ./.env or, failing that, a repo-root .env one level up.
config({ path: fileURLToPath(new URL("../.env", import.meta.url)) });
config({ path: fileURLToPath(new URL("../../.env", import.meta.url)) });

// Opik's judge goes through the Vercel AI SDK provider, which also honours
// ANTHROPIC_BASE_URL. A leftover proxy value there makes every judge call 404,
// so talk to the real API.
delete process.env.ANTHROPIC_BASE_URL;
