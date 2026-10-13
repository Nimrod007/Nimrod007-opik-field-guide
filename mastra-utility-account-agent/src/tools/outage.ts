import { createTool } from "@mastra/core/tools";
import { z } from "zod";
import { ACCOUNTS, FILED_REPORTS, KNOWN_OUTAGES } from "../data/accounts.ts";

export function checkKnownOutage(accountId: string, kind: "electricity" | "water") {
  const account = ACCOUNTS[accountId.toUpperCase().trim()];
  if (!account) return { error: `No account ${accountId}.` };
  const outage = KNOWN_OUTAGES.find((o) => o.zone === account.serviceZone && o.kind === kind);
  return outage ? { known: true, ...outage } : { known: false, zone: account.serviceZone };
}

export function fileOutageReport(accountId: string, kind: "electricity" | "water", details: string) {
  const account = ACCOUNTS[accountId.toUpperCase().trim()];
  if (!account) return { error: `No account ${accountId}.` };
  const ticketId = `OUT-${String(FILED_REPORTS.length + 1).padStart(4, "0")}`;
  FILED_REPORTS.push({ ticketId, accountId: account.accountId, kind, details });
  return { ticketId, accountId: account.accountId, kind, status: "crew-notified" };
}

export const checkOutageTool = createTool({
  id: "check_known_outage",
  description: "Check whether the utility already has a published outage for the account's service zone.",
  inputSchema: z.object({
    account_id: z.string(),
    kind: z.enum(["electricity", "water"]),
  }),
  execute: async ({ account_id, kind }) => checkKnownOutage(account_id, kind),
});

export const reportOutageTool = createTool({
  id: "report_outage",
  description:
    "File a new outage report. Only call this after check_known_outage shows nothing published for the zone.",
  inputSchema: z.object({
    account_id: z.string(),
    kind: z.enum(["electricity", "water"]),
    details: z.string().describe("What the customer is seeing"),
  }),
  execute: async ({ account_id, kind, details }) => fileOutageReport(account_id, kind, details),
});
