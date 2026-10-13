import { describe, expect, it } from "vitest";

// With tracking disabled the Mastra instance builds without any exporter, so the traced app
// can be exercised offline: no Opik, no provider key.
process.env.OPIK_TRACK_DISABLE = "true";

describe("traced app with tracking disabled", () => {
  it("builds the Mastra instance and runs a registered tool through it", async () => {
    const { mastra, trackingDisabled } = await import("../src/mastra.ts");
    expect(trackingDisabled).toBe(true);
    const agent = mastra.getAgent("accountAgent");
    const tools: any = await agent.listTools();
    expect(Object.keys(tools).sort()).toEqual(
      ["checkOutageTool", "meterReadingTool", "reportOutageTool", "usageHistoryTool"].sort(),
    );
    const out: any = await tools.meterReadingTool.execute({ account_id: "HL-31977", kind: "water" }, {});
    expect(out.meterId).toBe("W-30901");
  });
});
