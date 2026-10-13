// One command, end to end: ensure the online-eval rule, build and boot the SvelteKit server,
// play scripted multi-turn streaming conversations, shut the server down (which flushes the
// spans to Opik), then wait for the rule's scores to appear on the new traces.
import { spawn, spawnSync } from "node:child_process";
import { setTimeout as sleep } from "node:timers/promises";
import { randomUUID } from "node:crypto";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { config } from "dotenv";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
config({ path: path.join(root, ".env"), quiet: true });
config({ path: path.join(root, "..", ".env"), quiet: true });

if (!process.env.OPENAI_API_KEY) {
  console.error("Missing OPENAI_API_KEY. Copy .env.example to .env and fill it in.");
  process.exit(1);
}
const { api } = await import("./opik-rest.mjs");
const { ensureRule, PROJECT, RULE } = await import("./ensure-rule.mjs");

const PORT = process.env.DEMO_PORT || "4191";
const BASE = `http://127.0.0.1:${PORT}`;

const conversations = [
  {
    title: "A meteor-shower weekend",
    turns: [
      "I want to watch a meteor shower in November. Which one should I plan for, and when?",
      "Where in the sky should I look, and what time of night is best?",
    ],
  },
  {
    title: "Planets and a lunar eclipse",
    turns: [
      "Is Jupiter doing anything worth staying up for in December?",
      "Do I need a telescope for the lunar eclipse in January?",
    ],
  },
  {
    title: "Something the calendar does not list",
    turns: [
      "When is the next total solar eclipse I can see from my backyard?",
      "OK, then what's a good beginner telescope under 300 dollars?",
    ],
  },
];

// 1) The rule must exist and be enabled BEFORE any trace arrives.
const rule = await ensureRule();
console.log(`Online-eval rule "${RULE}" ${rule.created ? "created" : "already present"} (${rule.id}).`);

// 2) Build and boot the production server (adapter-node).
console.log("Building...");
const build = spawnSync("npx", ["vite", "build"], { cwd: root, stdio: "ignore" });
if (build.status !== 0) throw new Error("vite build failed");
console.log(`Starting server on port ${PORT}...`);
const server = spawn("node", ["build"], {
  cwd: root,
  env: { ...process.env, PORT, HOST: "127.0.0.1" },
  stdio: ["ignore", "pipe", "pipe"],
});
server.stderr.on("data", (d) => process.stderr.write(d));
server.stdout.on("data", (d) => process.stderr.write(d));
const exited = new Promise((resolve) => server.on("exit", resolve));

async function waitForServer(timeoutMs = 30_000) {
  const deadline = Date.now() + timeoutMs; let lastError;
  while (Date.now() < deadline) {
    try {
      const res = await fetch(BASE, { signal: AbortSignal.timeout(2000) });
      if (res.ok) return;
      lastError = `HTTP ${res.status} ${(await res.text()).slice(0, 300)}`;
    } catch (e) { lastError = e; }
    await sleep(300);
  }
  throw new Error("Server did not become ready in time: " + lastError?.cause?.message + lastError);
}

// POST the whole history (what the Chat class does) and read the UI-message SSE stream.
async function chatTurn(chatId, messages) {
  const res = await fetch(`${BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: chatId, messages }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  let text = "", buffer = "";
  const decoder = new TextDecoder();
  for await (const chunk of res.body) {
    buffer += decoder.decode(chunk, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      if (!line.startsWith("data: ") || line === "data: [DONE]") continue;
      try {
        const event = JSON.parse(line.slice(6));
        if (event.type === "text-delta" && event.delta) {
          text += event.delta;
          process.stdout.write(event.delta);
        }
      } catch { /* ignore keepalives */ }
    }
  }
  process.stdout.write("\n");
  return text;
}

const message = (role, text) => ({ id: randomUUID(), role, parts: [{ type: "text", text }] });
const startedAt = new Date().toISOString();

try {
  await waitForServer();
  for (const conversation of conversations) {
    const chatId = randomUUID();
    console.log(`\n=== ${conversation.title} (thread ${chatId.slice(0, 8)}) ===`);
    const history = [];
    for (const turn of conversation.turns) {
      console.log(`\nYou: ${turn}\nNova: `);
      history.push(message("user", turn));
      history.push(message("assistant", await chatTurn(chatId, history)));
    }
  }
} finally {
  // SIGTERM makes adapter-node emit sveltekit:shutdown, where the OTel SDK flushes to Opik.
  server.kill("SIGTERM");
  await Promise.race([exited, sleep(15_000)]);
  if (server.exitCode === null) server.kill("SIGKILL");
}

// 3) Wait for the online-eval rule to score the new traces.
console.log("\nWaiting for the online-eval rule to score the traces...");
let traces = [];
for (let i = 0; i < 24; i++) {
  await sleep(5000);
  const res = await api("GET", `v1/private/traces?project_name=${encodeURIComponent(PROJECT)}&size=100`);
  // The judge's own runs also land in the project as "online_evaluation" traces; skip them here.
  traces = (res.content ?? []).filter((t) => t.start_time >= startedAt && t.name === "stargazing-turn");
  const scored = traces.filter((t) => (t.feedback_scores ?? []).length > 0);
  if (traces.length >= 6 && scored.length === traces.length) break;
}
const scored = traces.filter((t) => (t.feedback_scores ?? []).length > 0);
console.log(`${traces.length} traces in "${PROJECT}", ${scored.length} scored by "${RULE}":`);
for (const t of traces) {
  const s = (t.feedback_scores ?? []).map((f) => `${f.name}=${f.value}`).join(", ") || "(no score yet)";
  console.log(`  ${t.name}  thread=${(t.thread_id ?? "").slice(0, 8)}  ${s}`);
}
if (scored.length === 0) {
  console.error("No scores landed. Check the rule's logs in Opik (Online evaluation tab) for the judge error.");
  process.exit(1);
}
