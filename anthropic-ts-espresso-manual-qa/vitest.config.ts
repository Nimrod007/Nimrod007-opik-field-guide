import { defineConfig } from "vitest/config";

export default defineConfig({
  // OPIK_TRACK_DISABLE turns track() into a pass-through, so tests never hit Opik.
  test: { env: { OPIK_TRACK_DISABLE: "true" } },
});
