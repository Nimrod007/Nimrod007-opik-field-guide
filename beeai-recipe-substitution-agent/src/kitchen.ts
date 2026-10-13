// Pure kitchen logic: pantry lookup, substitution table, unit conversion.
// All data is fictional and read from data/, so only the LLM call leaves your machine.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const load = <T>(file: string): T =>
  JSON.parse(readFileSync(fileURLToPath(new URL(`../data/${file}`, import.meta.url)), "utf8")) as T;

type PantryItem = { name: string; amount: number; unit: string };
type Substitution = { substitute: string; ratio: string; needs: string[]; notes: string };
type Densities = {
  volume_ml: Record<string, number>;
  grams_per_ml: Record<string, number>;
  grams_per_each: Record<string, number>;
};

const pantry = load<{ household: string; items: PantryItem[] }>("pantry.json");
const substitutions = load<Record<string, Substitution[]>>("substitutions.json");
const densities = load<Densities>("densities.json");

export const VOLUME_UNITS: [string, ...string[]] = ["ml", "l", "tsp", "tbsp", "cup", "g", "each"];

const norm = (s: string) => s.trim().toLowerCase().replace(/^\d+\s*/, "").replace(/s$/, "");

/** How much of an ingredient is in the pantry (0 when it is listed but used up, null when unknown). */
export function pantryLookup(ingredient: string): { ingredient: string; in_stock: boolean; amount: number; unit: string } | { ingredient: string; error: string } {
  const want = norm(ingredient);
  const hit = pantry.items.find((i) => norm(i.name) === want);
  if (!hit) return { ingredient, error: `"${ingredient}" is not tracked in the pantry list.` };
  return { ingredient: hit.name, in_stock: hit.amount > 0, amount: hit.amount, unit: hit.unit };
}

/** Candidate substitutes for a missing ingredient, each flagged with whether the pantry covers it. */
export function substitutionTable(ingredient: string) {
  const key = Object.keys(substitutions).find((k) => norm(k) === norm(ingredient));
  if (!key) return { ingredient, error: `No substitution known for "${ingredient}".`, known: Object.keys(substitutions) };
  return {
    ingredient: key,
    options: substitutions[key].map((s) => ({
      ...s,
      can_make_now: s.needs.every((n) => {
        const p = pantryLookup(n);
        return "in_stock" in p && p.in_stock;
      }),
    })),
  };
}

/** Convert between volume units, grams and "each" for a named ingredient. */
export function convertUnits(amount: number, from: string, to: string, ingredient: string) {
  const ing = norm(ingredient);
  if (from === to) return { amount, unit: to, ingredient };
  const eachG = densities.grams_per_each[ing];
  if (from === "each" && to === "g" && eachG) return { amount: amount * eachG, unit: to, ingredient };
  const d = densities.grams_per_ml[ing];
  const toMl = (a: number, u: string): number | undefined => {
    if (u in densities.volume_ml) return a * densities.volume_ml[u];
    if (u === "g" && d) return a / d;
    return undefined;
  };
  const ml = toMl(amount, from);
  if (ml === undefined) return { error: `Cannot convert ${from} of "${ingredient}": no density on file.` };
  let out: number;
  if (to in densities.volume_ml) out = ml / densities.volume_ml[to];
  else if (to === "g") {
    if (!d) return { error: `No density for "${ingredient}" to get grams.` };
    out = ml * d;
  } else return { error: `Unsupported target unit "${to}".` };
  return { amount: Math.round(out * 100) / 100, unit: to, ingredient };
}
