// Two versions of the managed illustration brief (Mustache templates).
// v1 is what a first draft looks like; v2 adds the rules an art director would
// write after seeing v1's pages side by side.

export const PROMPT_NAME = "storybook-illustration-brief";

export const BRIEF_V1 = `Illustration for a children's picture book page titled "{{title}}".
Main character: {{hero}}.
Scene: {{hero}} {{scene}}.
Mood: {{mood}}.`;

export const BRIEF_V2 = `Illustration for a children's picture book page titled "{{title}}".

Main character: {{hero}}, always drawn with {{hero_look}}.
Scene: {{hero}} {{scene}}.
Mood: {{mood}}.

House style: soft watercolor with visible paper grain, a warm limited palette of
amber, moss green and twilight blue, gentle rounded shapes, wide framing with calm
empty space at the top of the page.
Rules: do not draw any letters, words or signs anywhere in the image; no scary or
sharp elements; keep the character the same size and design as on every other page.`;

export const V1_CHANGE = "First draft: character, scene, mood";
export const V2_CHANGE =
  "Pin the character's look, add watercolor house style, ban lettering, reserve space for page text";

// Ordered list the library registers, oldest first.
export const BRIEF_VERSIONS = [
  { label: "v1", template: BRIEF_V1, changeDescription: V1_CHANGE },
  { label: "v2", template: BRIEF_V2, changeDescription: V2_CHANGE },
] as const;
