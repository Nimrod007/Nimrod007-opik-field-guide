import { Mastra } from "@mastra/core/mastra";
import { accountAgent } from "./agents/account-agent.ts";

export const mastra = new Mastra({
  agents: { accountAgent },
});
