import { openai } from "@ai-sdk/openai";
import { streamText, convertToModelMessages, tool, stepCountIs, type UIMessage } from "ai";
import { z } from "zod";
import { OpikExporter } from "opik-vercel";
import { loadEvents, searchEvents, SYSTEM_PROMPT } from "../../../lib/sky";
import type { RequestHandler } from "./$types";

export const POST: RequestHandler = async ({ request }) => {
  // The Chat class sends the chat id and the full history on every request.
  const { id, messages }: { id: string; messages: UIMessage[] } = await request.json();

  const result = streamText({
    model: openai("gpt-4o-mini"),
    system: SYSTEM_PROMPT,
    messages: await convertToModelMessages(messages),
    tools: {
      // Executed tools show up in Opik as tool spans between the two llm spans of the turn.
      lookupSkyEvents: tool({
        description: "Search the club's sky-events calendar by keyword and/or ISO date range.",
        inputSchema: z.object({
          keyword: z.string().optional(),
          from: z.string().optional().describe("inclusive ISO date, yyyy-mm-dd"),
          to: z.string().optional().describe("inclusive ISO date, yyyy-mm-dd"),
        }),
        execute: async (query) => searchEvents(loadEvents(), query),
      }),
    },
    stopWhen: stepCountIs(4),

    // runtimeContext.threadId becomes the Opik thread id via enrichSpan (src/lib/telemetry.ts);
    // getSettings() enables telemetry and names the trace, so the Traces table shows
    // "stargazing-turn" instead of a generic operation name.
    runtimeContext: { threadId: id, traceName: "stargazing-turn" },
    experimental_telemetry: {
      ...OpikExporter.getSettings({ name: "stargazing-turn" }),
      includeRuntimeContext: { threadId: true, traceName: true },
    },
  });

  return result.toUIMessageStreamResponse();
};
