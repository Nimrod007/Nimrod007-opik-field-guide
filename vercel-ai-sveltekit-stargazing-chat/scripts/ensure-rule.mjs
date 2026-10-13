// Creates the online-evaluation rule (an LLM-as-judge) for this project, idempotently.
// Run it BEFORE the demo traffic: Opik only scores traces that arrive after the rule is enabled.
import { api } from "./opik-rest.mjs";

export const PROJECT = "vercel-ai-sveltekit-stargazing-chat";
export const RULE = "stargazing_answer_relevance";

export async function ensureRule() {
  // The rule's judge runs server-side, so it needs an OpenAI key in Opik's provider store.
  // This script only checks that one is registered; it never writes a credential.
  const keys = await api("GET", "v1/private/llm-provider-key");
  if (!(keys.content ?? []).some((k) => k.provider === "openai")) {
    throw new Error(
      "No OpenAI key in Opik's LLM provider store. Add one in Opik (Configuration > AI providers) so the judge can run.",
    );
  }

  // A rule is attached to a project id, and a project only exists after its first trace,
  // so create the (empty) project first when it is missing.
  const projects = await api("GET", `v1/private/projects?name=${encodeURIComponent(PROJECT)}&size=50`);
  let project = (projects.content ?? []).find((p) => p.name === PROJECT);
  if (!project) {
    await api("POST", "v1/private/projects", { name: PROJECT });
    const again = await api("GET", `v1/private/projects?name=${encodeURIComponent(PROJECT)}&size=50`);
    project = (again.content ?? []).find((p) => p.name === PROJECT);
  }

  // Look the rule up by name so re-running the demo never creates duplicates.
  const rules = await api("GET", `v1/private/automations/evaluators?project_id=${project.id}&size=100`);
  const existing = (rules.content ?? []).find((r) => r.name === RULE);
  if (existing) {
    if (!existing.enabled) {
      await api("PATCH", `v1/private/automations/evaluators/${existing.id}`, { enabled: true });
    }
    return { id: existing.id, created: false };
  }

  await api("POST", "v1/private/automations/evaluators", {
    name: RULE,
    project_id: project.id,
    project_ids: [project.id],
    sampling_rate: 1.0,
    enabled: true,
    type: "llm_as_judge",
    code: {
      model: { name: "gpt-4o-mini", temperature: 0.0 },
      messages: [
        {
          role: "SYSTEM",
          content:
            "You judge a backyard-astronomy club assistant. Decide whether the OUTPUT actually addresses what the user asked in the INPUT (the last user message matters most). Score 1 if the reply is on-topic and answers, or honestly says the calendar does not list it and offers general stargazing advice; score 0 if it is off-topic, evasive, or answers a different question.",
        },
        { role: "USER", content: "INPUT:\n{{input}}\n\nOUTPUT:\n{{output}}" },
      ],
      variables: { input: "input", output: "output" },
      schema: [
        { name: "answer_relevance", type: "INTEGER", description: "1 if the reply addresses the question, else 0" },
      ],
    },
  });
  const after = await api("GET", `v1/private/automations/evaluators?project_id=${project.id}&size=100`);
  const created = (after.content ?? []).find((r) => r.name === RULE);
  return { id: created.id, created: true };
}
