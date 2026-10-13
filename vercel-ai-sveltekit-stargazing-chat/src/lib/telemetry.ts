// The whole Opik integration for the server lives here.
import { NodeSDK } from "@opentelemetry/sdk-node";
import { registerTelemetry } from "ai";
import { OpenTelemetry } from "@ai-sdk/otel";
import { OpikExporter } from "opik-vercel";
import { Opik } from "opik";

export const PROJECT_NAME = "vercel-ai-sveltekit-stargazing-chat";

/** Copies the thread id / trace name that the route puts in runtimeContext onto span attributes. */
export function enrich(runtimeContext?: Record<string, unknown>): Record<string, string> {
  const attributes: Record<string, string> = {};
  if (runtimeContext?.threadId != null) {
    attributes["ai.telemetry.metadata.threadId"] = String(runtimeContext.threadId);
  }
  if (runtimeContext?.traceName != null) {
    attributes["ai.telemetry.metadata.traceName"] = String(runtimeContext.traceName);
  }
  return attributes;
}

let sdk: NodeSDK | undefined;

export function setupTelemetry(): void {
  if (sdk) return;

  // OpikExporter is an OpenTelemetry span exporter: it turns AI SDK spans into Opik traces
  // (root = streamText call) with llm spans (usage + cost) and tool spans below. Pinning the
  // project here means every trace lands in one Opik project; URL/workspace come from OPIK_* env.
  const exporter = new OpikExporter({
    client: new Opik({ projectName: PROJECT_NAME }),
    tags: ["sveltekit", "streaming"],
  });
  sdk = new NodeSDK({ serviceName: PROJECT_NAME, traceExporter: exporter });
  sdk.start();

  // AI SDK v7 only emits spans after this explicit registration; without it the exporter
  // receives nothing and the project stays empty. enrichSpan carries the chat id to Opik's
  // thread_id, which is what groups separate HTTP requests into one thread.
  registerTelemetry(
    new OpenTelemetry({
      usage: true,
      enrichSpan: ({ runtimeContext }) => enrich(runtimeContext as Record<string, unknown> | undefined),
    }),
  );

  // adapter-node emits this on SIGTERM/SIGINT; shutting the SDK down flushes batched spans to
  // Opik. Skip it and the last turns of a short-lived server never arrive.
  process.on("sveltekit:shutdown" as NodeJS.Signals, async () => {
    await sdk?.shutdown();
  });
}
