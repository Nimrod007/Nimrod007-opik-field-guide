import "./env.js";
import { answerQuestion } from "./qa.js";
import { QUESTIONS } from "./questions.js";

const question = QUESTIONS[0]!;
console.log(`Q: ${question}`);
console.log(`A: ${await answerQuestion(question)}`);
