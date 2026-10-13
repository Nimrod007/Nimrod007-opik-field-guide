// Wires BeeAI to Opik over plain OpenTelemetry: no Opik SDK, only OTLP headers.
import { NodeSDK } from "@opentelemetry/sdk-node";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { BeeAIInstrumentation } from "@arizeai/openinference-instrumentation-beeai";
import * as beeaiFramework from "beeai-framework";

export const OPIK_PROJECT = "beeai-recipe-substitution-agent";

export type Tracing = { shutdown: () => Promise<void>; enabled: boolean };

export function startTracing(env: NodeJS.ProcessEnv = process.env): Tracing {
  // OTEL_SDK_DISABLED=true is the standard OTel switch; tests and offline runs use it to skip tracing.
  if (env.OTEL_SDK_DISABLED === "true") return { enabled: false, shutdown: async () => {} };

  const apiBase = (env.OPIK_URL_OVERRIDE ?? "https://www.comet.com/opik/api").replace(/\/+$/, "");
  const headers: Record<string, string> = {
    // Comet-Workspace routes to the workspace; projectName decides which Opik project receives the traces.
    "Comet-Workspace": env.OPIK_WORKSPACE ?? "default",
    projectName: OPIK_PROJECT,
  };
  // Opik Cloud needs the key; a local self-hosted Opik takes no Authorization header.
  if (env.OPIK_API_KEY) headers.Authorization = env.OPIK_API_KEY;

  // BeeAIInstrumentation emits OpenInference spans: a root run span, one iteration-N span per ReAct turn, llm spans for model calls and spans for tool runs.
  const instrumentation = new BeeAIInstrumentation();
  const sdk = new NodeSDK({
    traceExporter: new OTLPTraceExporter({ url: `${apiBase}/v1/private/otel/v1/traces`, headers }),
    instrumentations: [instrumentation],
  });
  sdk.start();
  // Under tsx beeai-framework is loaded before the module hook can patch it; patch it explicitly,
  // otherwise no BeeAI spans are produced at all.
  instrumentation.manuallyInstrument(beeaiFramework);

  // sdk.shutdown() flushes the batch exporter; skip it and the last request's spans never reach Opik.
  return { enabled: true, shutdown: () => sdk.shutdown() };
}
