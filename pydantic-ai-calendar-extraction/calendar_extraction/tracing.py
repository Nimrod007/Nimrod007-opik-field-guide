"""Opik wiring: Pydantic AI -> logfire -> OpenTelemetry -> Opik's OTLP endpoint."""

import os

PROJECT_NAME = "pydantic-ai-calendar-extraction"
# Local self-hosted Opik. For Opik Cloud use https://www.comet.com/opik/api/v1/private/otel
# and add Authorization=<api key> to the headers.
DEFAULT_OTLP_ENDPOINT = "http://localhost:5173/api/v1/private/otel"


def setup_tracing() -> None:
    """Send every Pydantic AI span to Opik. Call once, before the first agent run."""
    # The OTLP exporter reads these env vars: endpoint says where Opik lives, and the
    # projectName header decides which Opik project the traces land in (without it
    # they go to "Default Project").
    os.environ["OPIK_PROJECT_NAME"] = PROJECT_NAME
    os.environ.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", DEFAULT_OTLP_ENDPOINT)
    os.environ.setdefault(
        "OTEL_EXPORTER_OTLP_HEADERS",
        f"Comet-Workspace={os.getenv('OPIK_WORKSPACE', 'default')},projectName={PROJECT_NAME}",
    )
    os.environ["OTEL_METRICS_EXPORTER"] = "none"

    import logfire
    from opik.integrations.otel import OpikSpanProcessor

    # OpikSpanProcessor ties the agent's OTel spans to the surrounding @opik.track
    # trace, so each extraction is ONE trace instead of loose OTel roots.
    logfire.configure(send_to_logfire=False, console=False, additional_span_processors=[OpikSpanProcessor()])
    # instrument_pydantic_ai makes every agent run emit invoke_agent / chat spans
    # carrying gen_ai.* attributes, which Opik maps to llm spans with usage.
    logfire.instrument_pydantic_ai()


def flush_tracing() -> None:
    """Push buffered spans out before the process exits; otherwise the tail of the run is lost."""
    import logfire
    import opik

    logfire.force_flush()
    opik.flush_tracker()
