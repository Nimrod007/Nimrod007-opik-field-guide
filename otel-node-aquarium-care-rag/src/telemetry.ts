import { context, SpanKind, SpanStatusCode, trace, type Attributes, type Span } from "@opentelemetry/api";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-proto";
import { resourceFromAttributes } from "@opentelemetry/resources";
import { BatchSpanProcessor, type SpanExporter } from "@opentelemetry/sdk-trace-base";
import { NodeTracerProvider } from "@opentelemetry/sdk-trace-node";

export const PROJECT = process.env.OPIK_PROJECT_NAME ?? "otel-node-aquarium-care-rag";
const OTLP_BASE = process.env.OTEL_EXPORTER_OTLP_ENDPOINT ?? "http://localhost:5173/api/v1/private/otel";

let provider: NodeTracerProvider | undefined;

/**
 * Plain OpenTelemetry, no Opik SDK. Opik ingests OTLP over HTTP/protobuf at /api/v1/private/otel;
 * the two headers choose the workspace and the project the traces land in (without projectName
 * they go to "Default Project"). Local Opik needs no Authorization header; Opik Cloud adds
 * `Authorization: <api key>`.
 */
export function initTelemetry(exporter?: SpanExporter): void {
  // Standard OTel kill switch: with no provider registered, every span call below is a no-op.
  if (provider || process.env.OTEL_SDK_DISABLED === "true") return;
  const headers: Record<string, string> = {
    "Comet-Workspace": process.env.OPIK_WORKSPACE ?? "default",
    projectName: PROJECT,
  };
  if (process.env.OPIK_API_KEY) headers.Authorization = process.env.OPIK_API_KEY;
  provider = new NodeTracerProvider({
    resource: resourceFromAttributes({ "service.name": "aquarium-care-rag" }),
    // The batch processor buffers spans; they are only guaranteed to leave the process on shutdown().
    spanProcessors: [new BatchSpanProcessor(exporter ?? new OTLPTraceExporter({ url: `${OTLP_BASE}/v1/traces`, headers }))],
  });
  // register() installs the AsyncLocalStorage context manager, which is what makes the retrieve and
  // chat spans nest under the HTTP request span (one trace per question) instead of becoming roots.
  provider.register();
}

/** Push buffered spans out now without stopping the SDK. */
export async function flushTelemetry(): Promise<void> {
  await provider?.forceFlush();
}

/** Flush and stop the exporter. Without this a short-lived process exits before the batch is sent. */
export async function shutdownTelemetry(): Promise<void> {
  await provider?.shutdown();
  trace.disable(); // release the global provider slot so telemetry can be initialised again (tests do this)
  provider = undefined;
}

/**
 * GenAI semantic conventions make prompt/completion capture opt-in because messages may hold
 * personal data. We honour the standard switch; unset it and spans carry usage but no text.
 */
export function captureContent(): boolean {
  return process.env.OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT === "true";
}

const tracer = () => trace.getTracer("aquarium-care-rag");

/** Run fn inside a child span of the active span; records errors and always ends the span. */
export async function withSpan<T>(
  name: string,
  attributes: Attributes,
  fn: (span: Span) => Promise<T>,
  kind: SpanKind = SpanKind.INTERNAL,
): Promise<T> {
  return tracer().startActiveSpan(name, { kind, attributes }, async (span) => {
    try {
      return await fn(span);
    } catch (err) {
      span.recordException(err as Error);
      span.setStatus({ code: SpanStatusCode.ERROR, message: String(err) });
      throw err;
    } finally {
      span.end();
    }
  });
}

export { context, trace };
