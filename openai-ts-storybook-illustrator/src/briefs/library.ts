import { Opik, PromptType, type Prompt } from "opik";
import { BRIEF_VERSIONS, PROMPT_NAME } from "./templates.js";

// Pure: which of our briefs still need creating, given the templates the library
// already holds? createPrompt only dedupes against the *latest* version, so on a
// re-run we must not blindly re-create v1 after v2 exists (that would mint a v3).
export function missingBriefs(existingTemplates: string[]) {
  const have = new Set(existingTemplates);
  return BRIEF_VERSIONS.filter((b) => !have.has(b.template));
}

// Registers v1 then v2 in the Opik prompt library (project-scoped) and returns
// the live Prompt objects, whose .version ("v1"/"v2") is stamped onto each trace.
export async function registerBriefs(
  opik: Opik,
  projectName: string,
): Promise<{ v1: Prompt; v2: Prompt }> {
  // getPrompt with projectName looks the prompt up in this project only.
  const current = await opik.getPrompt({ name: PROMPT_NAME, projectName });
  const existing = current ? (await current.getVersions()).map((v) => v.prompt) : [];

  for (const brief of missingBriefs(existing)) {
    // createPrompt adds a new prompt version in the library under this project;
    // the Prompts page shows each version with its change description.
    await opik.createPrompt({
      name: PROMPT_NAME,
      prompt: brief.template,
      type: PromptType.MUSTACHE,
      changeDescription: brief.changeDescription,
      tags: ["storybook", "illustration"],
      projectName,
    });
    console.log(`Registered ${PROMPT_NAME} ${brief.label} in the prompt library.`);
  }

  const v1 = await opik.getPrompt({ name: PROMPT_NAME, version: "v1", projectName });
  const v2 = await opik.getPrompt({ name: PROMPT_NAME, version: "v2", projectName });
  if (!v1 || !v2) throw new Error(`Prompt "${PROMPT_NAME}" is missing v1 or v2.`);

  // Prints the v1 -> v2 unified diff, the same one the prompt library UI shows.
  const versions = await v2.getVersions();
  const first = versions.find((v) => v.version === "v1");
  const second = versions.find((v) => v.version === "v2");
  if (first && second) second.compareTo(first);
  return { v1, v2 };
}
