import { describe, expect, it } from "vitest";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { Opik } from "opik";
import { missingBriefs } from "../src/briefs/library.js";
import { BRIEF_V1, BRIEF_V2 } from "../src/briefs/templates.js";
import { PAGES } from "../src/briefs/pages.js";
import { imageTraceOutput, toDataUri } from "../src/attach/image.js";
import { generateImage, type ImageClient } from "../src/render/openai.js";
import { illustratePage, outputFile, renderBrief } from "../src/render/pipeline.js";
import { parseVersions } from "../src/cli.js";

// Stub: no network, returns a 1x1 PNG.
const PNG = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg==";
const stub: ImageClient = { images: { generate: async () => ({ data: [{ b64_json: PNG }] }) } };
// Real mustache-style formatter standing in for a library Prompt.
const fakePrompt = (template: string, version: string) => ({
  id: "p1",
  version,
  format: (vars: Record<string, unknown>) =>
    template.replace(/{{(\w+)}}/g, (_, k) => String(vars[k] ?? "")),
});

describe("briefs", () => {
  it("only registers versions the library lacks (no duplicate v3 on re-run)", () => {
    expect(missingBriefs([]).map((b) => b.label)).toEqual(["v1", "v2"]);
    expect(missingBriefs([BRIEF_V1]).map((b) => b.label)).toEqual(["v2"]);
    expect(missingBriefs([BRIEF_V2, BRIEF_V1])).toEqual([]);
  });
  it("v2 fills every placeholder and pins the hero's look; v1 does not", () => {
    const v1 = renderBrief(fakePrompt(BRIEF_V1, "v1") as never, PAGES[0]);
    const v2 = renderBrief(fakePrompt(BRIEF_V2, "v2") as never, PAGES[0]);
    expect(v2).not.toContain("{{");
    expect(v2).toContain("rust-orange fur");
    expect(v1).not.toContain("rust-orange");
  });
});

describe("attach + render", () => {
  it("builds a data-URI trace output", () => {
    expect(toDataUri("AAAA")).toBe("data:image/png;base64,AAAA");
    expect(imageTraceOutput("AAAA", "m", "1x1").image.startsWith("data:image/png")).toBe(true);
  });
  it("generateImage returns base64 and rejects empty results", async () => {
    expect(await generateImage(stub, "x")).toBe(PNG);
    await expect(generateImage({ images: { generate: async () => ({ data: [] }) } }, "x")).rejects.toThrow();
  });
  it("illustratePage runs through a real Opik client with tracking disabled", async () => {
    process.env.OPIK_TRACK_DISABLE = "true"; // SDK-documented switch: traced calls become no-ops
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "sb-"));
    const opik = new Opik({ projectName: "unit-test" });
    const out = await illustratePage(opik, () => stub, fakePrompt(BRIEF_V2, "v2") as never, PAGES[0], dir);
    expect(out.file).toBe(outputFile(dir, "v2", PAGES[0]));
    expect(fs.readFileSync(out.file).length).toBeGreaterThan(10);
  });
});

describe("cli", () => {
  it("parses --version", () => {
    expect(parseVersions([])).toEqual(["v1", "v2"]);
    expect(parseVersions(["--version", "v2"])).toEqual(["v2"]);
    expect(() => parseVersions(["--version", "x"])).toThrow();
  });
});
