// The fictional story: "Pip and the Lantern Moth". Each page supplies the
// variables that the illustration brief template fills in.

export interface StoryPage {
  id: string;
  title: string;
  scene: string;
  mood: string;
}

// The recurring hero. v2 of the brief pins these details so Pip looks the same on every page.
export const HERO = {
  hero: "Pip, a small fox cub",
  hero_look:
    "rust-orange fur, a cream chest patch, a tiny green knitted scarf, round amber eyes",
} as const;

export const PAGES: StoryPage[] = [
  {
    id: "page-1-burrow",
    title: "Pip leaves the burrow",
    scene: "stepping out of a cosy burrow under an oak root at dusk, fireflies drifting past",
    mood: "curious and hopeful",
  },
  {
    id: "page-2-pond",
    title: "The Lantern Moth by the pond",
    scene: "sitting at a still pond while a large glowing moth lands on a lily pad",
    mood: "quiet wonder",
  },
];
