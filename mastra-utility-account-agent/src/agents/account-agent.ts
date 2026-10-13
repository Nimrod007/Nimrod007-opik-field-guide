import { Agent } from "@mastra/core/agent";
import { openai } from "@ai-sdk/openai";
import { meterReadingTool, usageHistoryTool, checkOutageTool, reportOutageTool } from "../tools/index.ts";

export const accountAgent = new Agent({
  id: "account-agent",
  name: "harborlight-account-agent",
  instructions:
    "You are the account assistant for Harborlight Utilities (electricity and water). " +
    "Never guess readings, usage or outage status: use the tools. " +
    "For a power or water problem, call check_known_outage first; only call report_outage when " +
    "nothing is published for the customer's zone. When asked about a bill or usage, call " +
    "get_usage_history and mention any water-spike month. Answer in 2-4 plain sentences.",
  model: openai("gpt-4o-mini"),
  tools: { meterReadingTool, usageHistoryTool, checkOutageTool, reportOutageTool },
});
