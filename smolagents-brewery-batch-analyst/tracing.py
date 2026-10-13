"""OpenTelemetry wiring that sends smolagents traces to Opik."""
import os

PROJECT_NAME = "smolagents-brewery-batch-analyst"
# Local self-hosted Opik. For Comet cloud use https://www.comet.com/opik/api/v1/private/otel
# plus an Authorization header; both can be overridden with the standard OTEL_* variables.
OTLP_ENDPOINT = "http://localhost:5173/api/v1/private/otel"


def tracing_disabled() -> bool:
    return os.getenv("OPIK_TRACK_DISABLE", "").lower() == "true"


def setup_tracing():
    """Instrument smolagents and export spans to Opik. Returns the provider (or None)."""
    if tracing_disabled():
        return None
    from openinference.instrumentation.smolagents import SmolagentsInstrumentor
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    # Opik's OTLP endpoint reads the workspace and target project from these headers;
    # without projectName the traces land in the "Default Project".
    exporter = OTLPSpanExporter(
        endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", OTLP_ENDPOINT).rstrip("/") + "/v1/traces",
        headers={"Comet-Workspace": os.getenv("OPIK_WORKSPACE", "default"), "projectName": PROJECT_NAME},
    )
    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(exporter))
    # SmolagentsInstrumentor patches CodeAgent: each run becomes one trace, each step a span,
    # each model call an llm span carrying the generated code, and each execution its log.
    SmolagentsInstrumentor().instrument(tracer_provider=provider)
    return provider


def flush_tracing(provider) -> None:
    """Export any queued spans; without this a short script can exit before they are sent."""
    if provider is not None:
        provider.force_flush()
        provider.shutdown()
