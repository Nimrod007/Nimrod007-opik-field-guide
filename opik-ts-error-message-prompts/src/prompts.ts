export const PROJECT_NAME = "opik-ts-error-message-prompts";
export const PROMPT_NAME = "error-to-ui-copy";
export const MODEL = "gpt-4o-mini";

// v1: the "obvious" first draft. It asks for friendliness and nothing else,
// and even tells the model to keep the technical details.
export const PROMPT_V1 = `You work on Tallyboard, a team task tracking web app.
You will receive a raw error message from the app's logs. Rewrite it so it
sounds friendly and polite for the person using the app. Keep the original
details so support can still diagnose the problem.`;

// v2: the same job with explicit rules that match the assertions below.
export const PROMPT_V2 = `You work on Tallyboard, a team task tracking web app.
You will receive a raw error message from the app's logs. Rewrite it as
copy for a toast shown to the person using the app. Rules:

- Use at most 2 sentences.
- Plain language only: never include error codes, HTTP status codes,
  exception or class names, file paths, hostnames, or stack frames.
- Say what the person can do next (retry, check a setting, contact their
  workspace admin), and never blame them.
- Output only the copy, with no quotes and no preamble.`;

export const CHANGE_V1 = "Initial version: friendly tone, keep technical details.";
export const CHANGE_V2 =
  "Add rules: max 2 sentences, no technical identifiers, one concrete next step, no blame.";

// The quality bar, written as plain-language assertions. An LLM judge checks
// each one against the raw error and the rewritten copy.
export const ASSERTIONS = [
  "The text contains no technical identifiers: no error codes, HTTP status codes, exception or class names, file paths, hostnames, or stack frames",
  "The text is 2 sentences or fewer",
  "The text tells the user something concrete they can do next (retry, check something, or contact someone)",
  "The text does not blame the user",
];
