import { createTool } from "@mastra/core/tools";
import { z } from "zod";
import { ACCOUNTS, USAGE } from "../data/accounts.ts";

export function getUsageHistory(accountId: string, months: number) {
  const account = ACCOUNTS[accountId.toUpperCase().trim()];
  if (!account) return { error: `No account ${accountId}. Ask the customer to re-check the number.` };
  const rows = USAGE[account.accountId].slice(-months);
  const avgWater = rows.reduce((s, r) => s + r.waterM3, 0) / rows.length;
  return {
    accountId: account.accountId,
    months: rows,
    averageWaterM3: Math.round(avgWater * 10) / 10,
    // Months where water use is >1.5x the window average, so the agent need not do the maths.
    waterSpikeMonths: rows.filter((r) => r.waterM3 > avgWater * 1.5).map((r) => r.month),
  };
}

export const usageHistoryTool = createTool({
  id: "get_usage_history",
  description:
    "Monthly electricity (kWh), water (m3) and bill totals for the most recent N months (max 6), " +
    "with any water-spike months flagged.",
  inputSchema: z.object({
    account_id: z.string().describe("Account number, like HL-20418"),
    months: z.number().int().min(1).max(6).describe("How many recent months to return"),
  }),
  execute: async ({ account_id, months }) => getUsageHistory(account_id, months),
});
