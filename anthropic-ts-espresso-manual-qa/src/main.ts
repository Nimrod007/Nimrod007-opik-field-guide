import "./env.js";
import { flushAll, Opik } from "opik";
import { answerQuestion } from "./qa.js";
import { QUESTIONS } from "./questions.js";
import { buildSuite, crossCheck, runSuite } from "./suite.js";
import { PROJECT_NAME } from "./tracing.js";

// 1. One traced answer, so you can see the quotes in the trace output.
const question = QUESTIONS[0]!;
console.log(`Q: ${question}\nA: ${await answerQuestion(question)}\n`);

// 2. The citation test suite.
const client = new Opik({ projectName: PROJECT_NAME });
const suite = await buildSuite(client);
const result = await runSuite(suite);

console.log(`Pass rate: ${((result.passRate ?? 0) * 100).toFixed(0)}% (${result.itemsPassed}/${result.itemsTotal} items passed)`);
for (const item of result.itemResults.values()) {
  const first = item.testResults[0]!;
  const out = first.testCase.taskOutput as { input: { question: string }; output: string };
  console.log(`  [${item.passed ? "PASS" : "FAIL"}] ${out.input.question}  (${item.runsPassed}/${item.runsTotal} runs)`);
  const fake = crossCheck(String(out.output));
  if (fake.length) console.log(`         non-verbatim quotes: ${fake.length}`);
  if (!item.passed) {
    for (const run of item.testResults)
      for (const s of run.scoreResults)
        if (s.scoringFailed || s.value !== 1) console.log(`         failed: ${s.name} - ${s.reason}`);
  }
}
if (result.experimentUrl) console.log(`\nView the run: ${result.experimentUrl}`);

// Traces and experiment items are sent in batches; flush before exit.
await flushAll();
await client.flush();
