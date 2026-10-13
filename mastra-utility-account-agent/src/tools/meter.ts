import { createTool } from "@mastra/core/tools";
import { z } from "zod";
import { ACCOUNTS, READINGS } from "../data/accounts.ts";

// Plain function so tests can call it without a Mastra runtime.
export function getMeterReading(accountId: string, kind: "electricity" | "water") {
  const account = ACCOUNTS[accountId.toUpperCase().trim()];
  if (!account) return { error: `No account ${accountId}. Ask the customer to re-check the number.` };
  const reading = READINGS[account.meters[kind]];
  return { accountId: account.accountId, address: account.address, ...reading };
}

export const meterReadingTool = createTool({
  id: "get_meter_reading",
  description:
    "Latest recorded meter reading for an account's electricity or water meter " +
    "(meter id, reading, unit, date it was read).",
  inputSchema: z.object({
    account_id: z.string().describe("Account number, like HL-20418"),
    kind: z.enum(["electricity", "water"]),
  }),
  execute: async ({ account_id, kind }) => getMeterReading(account_id, kind),
});
