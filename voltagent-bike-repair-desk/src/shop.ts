// Fictional data and three tools for Spoke & Sprocket Cycle Works. Everything
// is in memory, so only the LLM call leaves your machine.
import { createTool } from "@voltagent/core";
import { z } from "zod";

export type Part = { sku: string; name: string; fits: string; price_usd: number; stock: number };

export const PARTS: Part[] = [
  { sku: "BRK-110", name: "Hydraulic disc brake pads (pair)", fits: "disc brakes", price_usd: 28, stock: 14 },
  { sku: "CHN-212", name: "11-speed chain", fits: "11-speed drivetrain", price_usd: 34, stock: 9 },
  { sku: "CAS-118", name: "11-speed cassette 11-34t", fits: "11-speed drivetrain", price_usd: 62, stock: 0 },
  { sku: "TUB-700", name: "700x32c inner tube", fits: "road and gravel wheels", price_usd: 9, stock: 40 },
  { sku: "TIR-700", name: "700x32c puncture-resistant tire", fits: "road and gravel wheels", price_usd: 46, stock: 5 },
  { sku: "CBL-200", name: "Shifter cable and housing kit", fits: "any derailleur", price_usd: 18, stock: 11 },
];

// Flat labor rates per job, in dollars.
export const LABOR_USD: Record<string, number> = {
  "brake service": 45,
  "drivetrain replacement": 85,
  "flat repair": 15,
  "gear tune-up": 40,
};

export const SLOTS: Record<string, string[]> = {
  "2026-11-02": ["09:00", "13:00"],
  "2026-11-03": ["10:00"],
  "2026-11-04": [],
};

export const bookings: { id: string; customer: string; date: string; time: string; job: string }[] = [];

export function lookupPartsImpl(query: string): Part[] {
  const q = query.toLowerCase();
  const words = q.split(/\W+/).filter((w) => w.length > 2);
  return PARTS.filter((p) => {
    const hay = `${p.name} ${p.fits} ${p.sku}`.toLowerCase();
    return hay.includes(q) || words.some((w) => hay.includes(w));
  });
}

export function quoteRepairImpl(job: string, skus: string[]) {
  const labor = LABOR_USD[job.toLowerCase()];
  if (labor === undefined) return { error: `unknown job "${job}"`, known_jobs: Object.keys(LABOR_USD) };
  const chosen = skus.map((s) => PARTS.find((p) => p.sku === s));
  const missing = skus.filter((_, i) => !chosen[i]);
  if (missing.length) return { error: `unknown sku: ${missing.join(", ")}` };
  const parts_usd = chosen.reduce((sum, p) => sum + p!.price_usd, 0);
  return { job, labor_usd: labor, parts_usd, total_usd: labor + parts_usd, out_of_stock: chosen.filter((p) => p!.stock === 0).map((p) => p!.sku) };
}

export function bookSlotImpl(customer: string, date: string, time: string, job: string) {
  const open = SLOTS[date];
  if (!open || !open.includes(time)) return { booked: false, reason: "slot not available", open_slots: open ?? [] };
  open.splice(open.indexOf(time), 1); // take the slot off the board
  const id = `RB-${3100 + bookings.length + 1}`;
  bookings.push({ id, customer, date, time, job });
  return { booked: true, booking_id: id, customer, date, time, job };
}

export const lookupParts = createTool({
  name: "lookup_parts",
  description: "Look up parts by keyword and return price and units in stock.",
  parameters: z.object({ query: z.string().describe("e.g. 'brake pads' or '11-speed'") }),
  execute: async ({ query }) => ({ matches: lookupPartsImpl(query) }),
});

export const quoteRepair = createTool({
  name: "quote_repair",
  description: "Quote a repair: flat labor for the job plus the listed part SKUs.",
  parameters: z.object({
    job: z.string().describe("one of: brake service, drivetrain replacement, flat repair, gear tune-up"),
    part_skus: z.array(z.string()).describe("SKUs from lookup_parts; may be empty"),
  }),
  execute: async ({ job, part_skus }) => quoteRepairImpl(job, part_skus),
});

export const bookSlot = createTool({
  name: "book_slot",
  description: "Book a bench slot. Dates are YYYY-MM-DD, times HH:MM. Open slots: " + JSON.stringify(SLOTS),
  parameters: z.object({
    customer: z.string(),
    date: z.string(),
    time: z.string(),
    job: z.string(),
  }),
  execute: async ({ customer, date, time, job }) => bookSlotImpl(customer, date, time, job),
});
