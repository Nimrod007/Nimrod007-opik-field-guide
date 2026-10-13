import { Opik, runTests, type TestSuite, type TestSuiteResult } from "opik";
import { answerQuestion, MANUAL, unverifiedQuotes } from "./qa.js";
import { PROJECT_NAME } from "./tracing.js";
import { GLOBAL_ASSERTIONS, ITEM_ASSERTIONS, QUESTIONS, UNANSWERABLE } from "./questions.js";

export const SUITE_NAME = "anthropic-ts-espresso-manual-qa";
// Cheap judge. Do not pass reasoning_effort in judge settings: it fails for this model.
export const JUDGE_MODEL = "claude-haiku-4-5-20251001";

export async function buildSuite(client: Opik): Promise<TestSuite> {
  // A test suite is an Opik dataset whose items carry assertions. Global
  // assertions apply to every item; this shows under Test suites in the project.
  const suite = await client.getOrCreateTestSuite({
    name: SUITE_NAME,
    projectName: PROJECT_NAME,
    globalAssertions: GLOBAL_ASSERTIONS,
    // Judges are noisy: each item runs 3 times and must pass at least 2.
    globalExecutionPolicy: { runsPerItem: 3, passThreshold: 2 },
  });
  // Items carry the question AND the manual so the judge can check quotes
  // against it. No expected answers: those would let the judge cheat.
  // getOrCreate + insert dedupes identical items on re-runs.
  await suite.insert(
    [...QUESTIONS, UNANSWERABLE].map((question) => ({
      data: { question, context: MANUAL },
      assertions: ITEM_ASSERTIONS[question] ?? [],
    })),
  );
  return suite;
}

export async function runSuite(suite: TestSuite): Promise<TestSuiteResult> {
  // runTests runs the task for every item, has the judge score each
  // assertion, and records one experiment with pass/fail per item. Each task
  // call is also a normal trace in the project.
  return runTests({
    testSuite: suite,
    projectName: PROJECT_NAME,
    // Name the run after the prompt variant so two runs are easy to compare.
    experimentName: `espresso-qa-${process.env.QA_PROMPT ?? "strict"}`,
    model: JUDGE_MODEL,
    taskThreads: 3,
    task: async (item) => {
      const question = String(item.question);
      const output = await answerQuestion(question);
      // input must be what the model saw (question + manual) so the judge can verify quotes.
      return { input: { question, context: MANUAL }, output };
    },
  });
}

/** Offline-friendly cross-check of the judge: quotes that are not substrings of the manual. */
export function crossCheck(output: string): string[] {
  return unverifiedQuotes(output);
}
