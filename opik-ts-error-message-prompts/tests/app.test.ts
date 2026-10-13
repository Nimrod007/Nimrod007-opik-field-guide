import { describe, expect, it, vi } from "vitest";
import type { Opik } from "opik";
import { ASSERTIONS, PROMPT_V1, PROMPT_V2 } from "../src/prompts.js";
import { RAW_ERRORS } from "../src/errors.js";
import { makeRewriter, rewriteWith } from "../src/rewrite.js";
import { registerPrompts } from "../src/suite.js";

describe("prompts and data", () => {
  it("v2 spells out every rule the suite asserts on; v1 does not", () => {
    for (const rule of ["at most 2 sentences", "never include error codes", "never blame"]) expect(PROMPT_V2).toContain(rule);
    expect(PROMPT_V1).not.toContain("at most");
    expect(ASSERTIONS).toHaveLength(4);
  });

  it("raw errors are distinct and look like stack-trace noise", () => {
    expect(new Set(RAW_ERRORS).size).toBe(RAW_ERRORS.length);
    expect(RAW_ERRORS.every((e) => /\d/.test(e) && e.length > 60)).toBe(true);
  });
});

describe("rewriting", () => {
  it("sends the prompt as system and the raw error as user", async () => {
    const call = vi.fn(async () => "ok");
    await rewriteWith("SYS", "boom", call);
    expect(call).toHaveBeenCalledWith("SYS", "Raw error:\nboom");
  });

  it("a track()-wrapped rewriter still returns its value with tracking disabled", async () => {
    expect(process.env.OPIK_TRACK_DISABLE).toBe("true");
    const rewrite = makeRewriter(async (v) => `prompt-${v ?? "latest"}`, async (sys, user) => `${sys}|${user}`);
    expect(await rewrite("x", "v1")).toBe("prompt-v1|Raw error:\nx");
  });
});

describe("registerPrompts", () => {
  function fakeClient(existing: string[]) {
    const created: string[] = [];
    const client = {
      getPrompt: async () => (existing.length ? { getVersions: async () => existing.map((prompt) => ({ prompt })) } : null),
      createPrompt: async (o: { prompt: string }) => void created.push(o.prompt),
    } as unknown as Opik;
    return { client, created };
  }

  it("creates v1 then v2 on an empty library", async () => {
    const { client, created } = fakeClient([]);
    await registerPrompts(client);
    expect(created).toEqual([PROMPT_V1, PROMPT_V2]);
  });

  it("creates nothing on a re-run, even though v1 differs from the latest version", async () => {
    const { client, created } = fakeClient([PROMPT_V2, PROMPT_V1]);
    await registerPrompts(client);
    expect(created).toEqual([]);
  });
});
