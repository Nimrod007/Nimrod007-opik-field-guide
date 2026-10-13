import { sveltekit } from "@sveltejs/kit/vite";
import adapter from "@sveltejs/adapter-node";
import { defineConfig } from "vite";

// SvelteKit 3 takes its configuration here instead of svelte.config.js.
export default defineConfig({
  plugins: [sveltekit({ adapter: adapter() })],
});
