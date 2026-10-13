import { Opik, runTests, type TestSuite, type TestSuiteResult, type Prompt } from "opik";
import { RAW_ERRORS } from "./errors.js";
import { ASSERTIONS, CHANGE_V1, CHANGE_V2, MODEL, PROJECT_NAME, PROMPT_NAME, PROMPT_V1, PROMPT_V2 } from "./prompts.js";
import { rewriteError } from "./rewrite.js";

// Cheap judge. Do not pass reasoning_effort in judge settings: it fails.
export const JUDGE_MODEL = "gpt-4o-mini";

/**
 * Register v1 and v2 in the prompt library, skipping any text the prompt already has.
 * createPrompt only compares against the LATEST version, so calling it with v1 and then v2 on
 * every run would keep adding v3, v4, ... (v1 differs from latest v2, then v2 differs from v1).
 */
export async function registerPrompts(client: Opik): Promise<void> {
  const known = new Set(
    ((await (await client.getPrompt({ name: PROMPT_NAME, projectName: PROJECT_NAME }))?.getVersions()) ?? []).map((v) => v.prompt),
  );
  for (const [text, changeDescription] of [[PROMPT_V1, CHANGE_V1], [PROMPT_V2, CHANGE_V2]] as const) {
    if (!known.has(text)) await client.createPrompt({ name: PROMPT_NAME, prompt: text, projectName: PROJECT_NAME, changeDescription });
  }
}

export async function buildSuite(client: Opik): Promise<TestSuite> {
  // A test suite is an Opik dataset whose items carry assertions; it shows
  // under Test suites in the project. Global assertions apply to every item.
  const suite = await client.getOrCreateTestSuite({
    name: PROMPT_NAME,
    projectName: PROJECT_NAME,
    globalAssertions: ASSERTIONS,
    // Judges are noisy: each item runs 3 times and must pass at least 2.
    globalExecutionPolicy: { runsPerItem: 3, passThreshold: 2 },
  });
  await suite.insert(RAW_ERRORS.map((rawError) => ({ data: { rawError } })));
  return suite;
}

export function runVersion(suite: TestSuite, prompt: Prompt, version: string): Promise<TestSuiteResult> {
  // runTests runs the task for every item, judges each assertion, and records
  // one experiment per call. `prompts` links the experiment to the exact prompt version.
  return runTests({
    testSuite: suite,
    projectName: PROJECT_NAME,
    experimentName: `${PROMPT_NAME}-${version}`,
    experimentConfig: { prompt_version: version, model: MODEL },
    prompts: [prompt],
    model: JUDGE_MODEL,
    taskThreads: 3,
    task: async (item) => {
      const rawError = String(item.rawError);
      // input must be what the judge should see next to the output.
      return { input: { rawError }, output: await rewriteError(rawError, version) };
    },
  });
}
