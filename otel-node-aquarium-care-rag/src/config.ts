import { config } from "dotenv";
import { existsSync } from "node:fs";
import { resolve } from "node:path";

// Load .env from the project folder or from the repo root (two levels up is the worktree root).
for (const p of [".env", "../.env"]) {
  if (existsSync(resolve(p))) config({ path: resolve(p), quiet: true });
}

export const CHAT_MODEL = "gpt-4o-mini";
export const EMBED_MODEL = "text-embedding-3-small";
export const TOP_K = 3;
