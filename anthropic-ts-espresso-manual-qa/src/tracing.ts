import type Anthropic from "@anthropic-ai/sdk";
import { track } from "opik";
import type { Messages } from "./qa.js";

export const PROJECT_NAME = "anthropic-ts-espresso-manual-qa";

/**
 * There is no official Opik wrapper for @anthropic-ai/sdk in TypeScript (the
 * Python SDK has track_anthropic; npm has no opik-anthropic), so we trace the
 * call by hand. track() with type "llm" makes each Messages call an llm span;
 * enrichSpan copies model, provider and token usage onto it. Without the
 * provider + usage fields the span shows no tokens and no cost.
 */
export function traceMessages(messages: Messages): Messages {
  const tracedCreate = track(
    {
      name: "anthropic.messages.create",
      projectName: PROJECT_NAME,
      type: "llm",
      enrichSpan: (message: Anthropic.Message) => ({
        model: message.model,
        provider: "anthropic",
        usage: {
          prompt_tokens: message.usage.input_tokens,
          completion_tokens: message.usage.output_tokens,
          total_tokens: message.usage.input_tokens + message.usage.output_tokens,
        },
      }),
    },
    (params: Anthropic.MessageCreateParamsNonStreaming) => messages.create(params),
  );
  return { create: tracedCreate };
}
