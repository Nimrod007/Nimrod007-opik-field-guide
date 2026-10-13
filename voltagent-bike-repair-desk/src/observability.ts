// The only file that knows tracing exists. VoltAgent's observability is plain
// OpenTelemetry, so spans reach Opik through an OTLP exporter plus a small
// attribute-mapping wrapper (see mapToGenAI).
import { VoltAgentObservability } from "@voltagent/core";
import { BatchSpanProcessor } from "@opentelemetry/sdk-trace-base";
import type { ReadableSpan, SpanExporter } from "@opentelemetry/sdk-trace-base";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";

type Attrs = Record<string, unknown>;

// VoltAgent writes `llm.usage.*` and `llm.model`; Opik reads `gen_ai.*`. Without
// this copy the llm spans arrive with no token usage. Opik prices a span only
// when it has usage AND a model AND a recognized provider, so the provider
// attribute is what turns tokens into a non-null total_estimated_cost.
export function mapToGenAI(attrs: Attrs, provider = "openai"): Attrs {
  if (attrs["span.type"] === "llm") {
    if (attrs["llm.model"]) attrs["gen_ai.request.model"] = attrs["llm.model"];
    attrs["gen_ai.provider.name"] = provider; // drives cost lookup in Opik
    for (const key of ["prompt_tokens", "completion_tokens", "total_tokens"]) {
      const value = attrs[`llm.usage.${key}`];
      if (value !== undefined) attrs[`gen_ai.usage.${key}`] = value; // usage on the llm span
    }
  } else if (attrs["span.type"] === "tool") {
    // Mirror the tool arguments to the GenAI name so Opik types the span as a
    // tool call and shows the arguments as its input.
    attrs["gen_ai.tool.call.arguments"] = attrs["input"] ?? "{}";
    delete attrs["input"];
    delete attrs["tool.parameters"]; // serialized zod schema, noise in the UI
  }
  return attrs;
}

class VoltAgentToGenAI implements SpanExporter {
  constructor(private readonly inner: SpanExporter, private readonly mapping: boolean) {}

  export(spans: ReadableSpan[], resultCallback: Parameters<SpanExporter["export"]>[1]): void {
    if (this.mapping) for (const span of spans) mapToGenAI(span.attributes as Attrs);
    this.inner.export(spans, resultCallback);
  }
  shutdown(): Promise<void> { return this.inner.shutdown(); }
  forceFlush(): Promise<void> { return this.inner.forceFlush?.() ?? Promise.resolve(); }
}

const endpoint = (process.env.OPIK_OTEL_ENDPOINT ?? "http://localhost:5173/api/v1/private/otel").replace(/\/+$/, "");
const disabled = process.env.OTEL_SDK_DISABLED === "true";

// Set OPIK_SKIP_MAPPING=true to see the unmapped baseline: spans still arrive,
// but with no usage and no cost.
const mapping = process.env.OPIK_SKIP_MAPPING !== "true";

export const observability = new VoltAgentObservability({
  serviceName: "voltagent-bike-repair-desk",
  // BatchSpanProcessor + OTLP exporter ships every VoltAgent span to Opik's
  // OTel endpoint; the headers pick the workspace and the project.
  spanProcessors: disabled
    ? []
    : [
        new BatchSpanProcessor(
          new VoltAgentToGenAI(
            new OTLPTraceExporter({
              url: `${endpoint}/v1/traces`,
              headers: {
                "Comet-Workspace": process.env.OPIK_WORKSPACE ?? "default",
                projectName: process.env.OPIK_PROJECT_NAME ?? "voltagent-bike-repair-desk",
                ...(process.env.OPIK_API_KEY ? { Authorization: process.env.OPIK_API_KEY } : {}),
              },
            }),
            mapping
          )
        ),
      ],
});
