import { Mastra } from "@mastra/core/mastra";
import { Observability } from "@mastra/observability";
import { OtelExporter } from "@mastra/otel-exporter";
import { LibSQLStore } from "@mastra/libsql";
import { accountAgent } from "./agents/account-agent.ts";

// Opik's OTLP base. Defaults to the local stack; OPIK_URL_OVERRIDE points at any other deployment.
const opikBase = (process.env.OPIK_URL_OVERRIDE ?? "http://localhost:5173/api").replace(/\/+$/, "");

export const OPIK_PROJECT = process.env.OPIK_PROJECT_NAME ?? "mastra-utility-account-agent";

// OPIK_TRACK_DISABLE=true leaves Mastra's observability unconfigured, so nothing is exported
// and no Opik is needed (the offline tests rely on this).
export const trackingDisabled = process.env.OPIK_TRACK_DISABLE === "true";

export const mastra = new Mastra({
  agents: { accountAgent },
  // Observability needs a storage backend to be enabled; in-memory is enough for a demo.
  storage: new LibSQLStore({ id: "memory-store", url: ":memory:" }),
  observability: trackingDisabled ? undefined : new Observability({
    configs: {
      default: {
        serviceName: OPIK_PROJECT,
        exporters: [
          // OtelExporter turns Mastra's agent/LLM/tool spans into OTLP and posts them to Opik's
          // OTel endpoint. Result: one trace per agent.generate() call with invoke_agent,
          // agent_step, chat and execute_tool spans. No tracing code in agents/ or tools/.
          new OtelExporter({
            provider: {
              custom: {
                endpoint: `${opikBase}/v1/private/otel/v1/traces`,
                protocol: "http/json",
                headers: {
                  // Selects the workspace. Local Opik needs no Authorization header; Opik Cloud
                  // would also need `Authorization: <api key>`.
                  "Comet-Workspace": process.env.OPIK_WORKSPACE ?? "default",
                  // Without projectName the traces go to the "Default Project" instead.
                  projectName: OPIK_PROJECT,
                  ...(process.env.OPIK_API_KEY ? { Authorization: process.env.OPIK_API_KEY } : {}),
                },
              },
            },
          }),
        ],
      },
    },
  }),
});
