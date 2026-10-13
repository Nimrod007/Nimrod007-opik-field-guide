export const QUESTIONS = [
  "How often should I descale, and can I use vinegar?",
  "What does error code E7 mean and what should I do?",
  "How much coffee goes in the double basket and how long should the shot take?",
  "What temperature should I steam milk to?",
  "How do I extend the warranty to 3 years?",
  "How often do I replace the water filter cartridge?",
];

// A question the manual does not cover: the right behaviour is to say so.
export const UNANSWERABLE = "Can I run the BL-7 on a 110V outlet in the UK?";

// Plain-English quality bar, checked by an LLM judge on every answer.
export const GLOBAL_ASSERTIONS = [
  "Every excerpt wrapped in <quote> tags in the response appears verbatim, character for character, in the provided manual context",
  "The quoted excerpts genuinely support the factual claims made in the answer",
  "The response answers the question that was asked",
];

// Item-level assertions pin down questions that have one correct answer.
export const ITEM_ASSERTIONS: Record<string, string[]> = {
  [QUESTIONS[0]!]: [
    "The response says to descale every 4 months, or every 2 months in hard water above 120 ppm",
    "The response says vinegar must not be used",
  ],
  [QUESTIONS[1]!]: [
    "The response says E7 means the brew boiler is overheating and tells the user to switch off, wait 30 minutes, and contact support if it returns",
  ],
  [UNANSWERABLE]: [
    "The response says the manual does not cover this and does not invent a voltage or compatibility answer",
  ],
};
