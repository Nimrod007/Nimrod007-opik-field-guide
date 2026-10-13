import { describe, it, expect } from "vitest";
import path from "node:path";
import { loadEvents, searchEvents } from "../src/lib/sky";
import { OpikExporter } from "opik-vercel";
import { enrich } from "../src/lib/telemetry";

const events = loadEvents(path.resolve(__dirname, "../data/sky-events.json"));

describe("searchEvents", () => {
  it("matches keywords case-insensitively in name or notes", () => {
    expect(searchEvents(events, { keyword: "METEOR" }).map((e) => e.event)).toContain("Leonid meteor shower peak");
  });
  it("applies an inclusive date range and sorts by date", () => {
    const r = searchEvents(events, { from: "2026-11-17", to: "2026-11-22" });
    expect(r.map((e) => e.date)).toEqual(["2026-11-17", "2026-11-22"]);
  });
  it("tolerates plurals and multi-word keywords", () => {
    expect(searchEvents(events, { keyword: "Leonids" })).toHaveLength(1);
    expect(searchEvents(events, { keyword: "lunar eclipse" })).toHaveLength(1);
  });
  it("returns nothing for an unknown event", () => {
    expect(searchEvents(events, { keyword: "supernova" })).toEqual([]);
  });
});

describe("enrich (traced-path helper, runs with tracking disabled)", () => {
  it("maps runtimeContext to the span attributes Opik reads", () => {
    expect(enrich({ threadId: "abc", traceName: "stargazing-turn" })).toEqual({
      "ai.telemetry.metadata.threadId": "abc",
      "ai.telemetry.metadata.traceName": "stargazing-turn",
    });
    expect(enrich(undefined)).toEqual({});
  });
});

describe("opik-vercel settings helper (works with tracking disabled and no keys)", () => {
  it("returns telemetry settings carrying the trace name", () => {
    const settings = OpikExporter.getSettings({ name: "stargazing-turn" });
    expect(settings.isEnabled).toBe(true);
    expect(JSON.stringify(settings)).toContain("stargazing-turn");
  });
});
