import { describe, expect, it, beforeEach } from "vitest";
import { getMeterReading } from "../src/tools/meter.ts";
import { getUsageHistory } from "../src/tools/usage.ts";
import { checkKnownOutage, fileOutageReport } from "../src/tools/outage.ts";
import { FILED_REPORTS } from "../src/data/accounts.ts";
import { SCRIPT } from "../src/script.ts";

beforeEach(() => {
  FILED_REPORTS.length = 0;
});

describe("tools", () => {
  it("returns the latest meter reading and tolerates sloppy ids", () => {
    const r: any = getMeterReading(" hl-20418 ", "electricity");
    expect(r.meterId).toBe("E-77120");
    expect(r.reading).toBe(48213);
  });

  it("returns an error object for an unknown account", () => {
    expect(getMeterReading("HL-00000", "water")).toHaveProperty("error");
  });

  it("flags the August water spike", () => {
    const r: any = getUsageHistory("HL-20418", 6);
    expect(r.waterSpikeMonths).toEqual(["2026-08"]);
    expect(getUsageHistory("HL-31977", 6)).toMatchObject({ waterSpikeMonths: [] });
  });

  it("knows the east-ridge outage but not north-bay", () => {
    expect(checkKnownOutage("HL-31977", "electricity")).toMatchObject({ known: true });
    expect(checkKnownOutage("HL-20418", "water")).toMatchObject({ known: false });
  });

  it("files numbered outage tickets", () => {
    expect(fileOutageReport("HL-20418", "water", "no pressure")).toMatchObject({ ticketId: "OUT-0001" });
    expect(fileOutageReport("HL-20418", "water", "again")).toMatchObject({ ticketId: "OUT-0002" });
  });

  it("ships a four-question script", () => {
    expect(SCRIPT).toHaveLength(4);
  });
});
