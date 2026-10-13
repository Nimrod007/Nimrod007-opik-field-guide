import "./config.js";
import { PROJECT } from "./telemetry.js";

// Reads the project back from Opik's REST API and checks what the OTLP export should have produced:
// one trace per question, llm spans with usage and cost, and the prompt/completion text on the chat span.
const API = (process.env.OPIK_URL_OVERRIDE ?? "http://localhost:5173/api/").replace(/\/?$/, "/");
const headers = { "Comet-Workspace": process.env.OPIK_WORKSPACE ?? "default" };

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API}v1/private/${path}`, { headers });
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
  return (await res.json()) as T;
}

interface Trace { id: string; name: string }
interface SpanRow {
  name: string; type: string; provider?: string;
  usage?: Record<string, number>; total_estimated_cost?: number; input?: unknown; output?: unknown;
}

const project = encodeURIComponent(PROJECT);
const traces = (await get<{ content: Trace[] }>(`traces?project_name=${project}&size=100`)).content;
console.log(`project ${PROJECT}: ${traces.length} traces`);
let problems = 0;
for (const t of traces) {
  const spans = (await get<{ content: SpanRow[] }>(`spans?project_name=${project}&trace_id=${t.id}&size=50`)).content;
  const chat = spans.find((s) => s.name.startsWith("chat "));
  const hasText = !!chat && JSON.stringify(chat.input ?? "").includes("messages") && JSON.stringify(chat.output ?? "").includes("content");
  const ok = !!chat && !!chat.usage?.prompt_tokens && !!chat.total_estimated_cost && hasText;
  if (t.name === "POST /ask" && !ok) problems++;
  console.log(
    `${t.name.padEnd(30)} spans=${spans.length} [${spans.map((s) => s.type).join(",")}] ` +
      `tokens=${chat?.usage?.prompt_tokens ?? "-"}+${chat?.usage?.completion_tokens ?? "-"} ` +
      `cost=$${chat?.total_estimated_cost?.toFixed(6) ?? "null"} provider=${chat?.provider ?? "-"} text=${hasText ? "yes" : "NO"}`,
  );
}
if (problems) {
  console.error(`${problems} question trace(s) lack usage, cost or prompt/completion text`);
  process.exit(1);
}
