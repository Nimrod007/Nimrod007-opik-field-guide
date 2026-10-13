import "./env.js";
import { flushAll } from "opik";
import { RAW_ERRORS } from "./errors.js";
import { PROMPT_NAME, PROJECT_NAME } from "./prompts.js";
import { opik, rewriteError } from "./rewrite.js";
import { buildSuite, registerPrompts, runVersion } from "./suite.js";

// 1. Prompt library: v1 and v2 of "error-to-ui-copy" (no duplicates on re-runs).
await registerPrompts(opik);
const prompt = (await opik.getPrompt({ name: PROMPT_NAME, projectName: PROJECT_NAME }))!;
console.log("Prompt versions in the library:");
for (const v of (await prompt.getVersions()).reverse()) console.log(`  ${v.version}  ${v.changeDescription}`);

// 2. One traced rewrite with the latest version.
console.log(`\nRaw:    ${RAW_ERRORS[0]}\nCopy:   ${await rewriteError(RAW_ERRORS[0]!)}\n`);

// 3. Run the same suite once per version.
const suite = await buildSuite(opik);
const summary: string[] = [];
for (const version of ["v1", "v2"]) {
  const p = (await opik.getPrompt({ name: PROMPT_NAME, version, projectName: PROJECT_NAME }))!;
  const result = await runVersion(suite, p, version);
  summary.push(`${PROMPT_NAME} ${version}: ${((result.passRate ?? 0) * 100).toFixed(0)}% pass rate (${result.itemsPassed}/${result.itemsTotal} items passed)`);
  for (const item of result.itemResults.values()) {
    const first = item.testResults[0]!;
    const out = first.testCase.taskOutput as { output: string };
    console.log(`  [${version} ${item.passed ? "PASS" : "FAIL"}] ${String(out.output).slice(0, 110).replace(/\n/g, " ")}`);
    if (!item.passed && version === "v2")
      for (const r of item.testResults) for (const s of r.scoreResults) if (s.scoringFailed || s.value !== 1) console.log(`         failed: ${s.name} - ${s.reason}`);
  }
  if (result.experimentUrl) summary.push(`  ${result.experimentUrl}`);
}
console.log("\n=== Prompt version comparison ===\n" + summary.join("\n"));

// Traces and experiment items are sent in batches; flush before exit.
await flushAll();
await opik.flush();
