// The substitution agent: a BeeAI ReAct agent on gpt-4o-mini with three kitchen tools.
// Each request gets a fresh agent and memory, so every request is an independent run.
import { ReActAgent } from "beeai-framework/agents/react/agent";
import { OpenAIChatModel } from "beeai-framework/adapters/openai/backend/chat";
import { UnconstrainedMemory } from "beeai-framework/memory/unconstrainedMemory";
import { kitchenTools } from "./tools.ts";

const INSTRUCTIONS = `You are a calm kitchen helper for home cooks who are missing an ingredient.

For the request below:
1. Use substitution_table to find substitutes for the missing ingredient.
2. Use pantry_lookup to confirm the cook really has what a substitute needs (the table's can_make_now flag is a hint, not a promise).
3. If the cook asks for grams or ml, use unit_conversion. Never do unit math in your head.
4. Recommend ONE substitute the cook can make right now, with the exact amount. If none is possible, say so and suggest what to buy.

Format your final answer exactly like this:
Missing: <ingredient>
Use: <substitute and exact amount>
Why it works: <one sentence>
Heads-up: <one sentence on taste or texture>`;

export function createAgent(): ReActAgent {
  return new ReActAgent({
    llm: new OpenAIChatModel("gpt-4o-mini"),
    tools: kitchenTools,
    memory: new UnconstrainedMemory(),
  });
}

export async function findSubstitution(request: string): Promise<string> {
  const agent = createAgent();
  const response = await agent.run(
    { prompt: `${INSTRUCTIONS}\n\nRequest: "${request}"` },
    { execution: { maxRetriesPerStep: 3, totalMaxRetries: 10, maxIterations: 10 } },
  );
  return response.result.text;
}
