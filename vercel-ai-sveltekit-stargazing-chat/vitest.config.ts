import { defineConfig } from "vitest/config";

// Offline tests only exercise plain TypeScript helpers, so no SvelteKit plugin is needed.
export default defineConfig({ test: { include: ["tests/**/*.test.ts"] } });
