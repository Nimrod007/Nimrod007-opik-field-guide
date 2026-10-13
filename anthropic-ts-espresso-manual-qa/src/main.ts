import "./env.js";
import { flushAll } from "opik";
import { answerQuestion } from "./qa.js";
import { QUESTIONS } from "./questions.js";

const question = QUESTIONS[0]!;
console.log(`Q: ${question}`);
console.log(`A: ${await answerQuestion(question)}`);

// Traces are sent in batches; flush before exit or the last ones are lost.
await flushAll();
