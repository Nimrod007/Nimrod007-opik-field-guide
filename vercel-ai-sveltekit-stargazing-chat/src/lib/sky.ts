// Pure helpers for the fictional sky-events calendar: no I/O besides reading the JSON file,
// so they are easy to unit-test and have nothing to do with Opik.
import { readFileSync } from "node:fs";
import path from "node:path";

export interface SkyEvent {
  date: string; // ISO yyyy-mm-dd
  event: string;
  bestTime: string;
  look: string;
  notes: string;
}

export function loadEvents(file = path.resolve(process.cwd(), "data/sky-events.json")): SkyEvent[] {
  return JSON.parse(readFileSync(file, "utf8")) as SkyEvent[];
}

export interface EventQuery {
  keyword?: string;
  from?: string;
  to?: string;
}

/** Filter by case-insensitive keyword (all words, in event name or notes) and an inclusive ISO date range. */
export function searchEvents(events: SkyEvent[], { keyword, from, to }: EventQuery): SkyEvent[] {
  // Every word of the keyword must appear (a trailing "s" is ignored, so "Leonids" finds "Leonid").
  const words = (keyword ?? "").toLowerCase().split(/\s+/).filter(Boolean).map((w) => w.replace(/s$/, ""));
  return events
    .filter((e) => words.every((w) => `${e.event} ${e.notes}`.toLowerCase().includes(w)))
    .filter((e) => !from || e.date >= from)
    .filter((e) => !to || e.date <= to)
    .sort((a, b) => a.date.localeCompare(b.date));
}

// The fictional "today": the model can't know the calendar's dates, so the prompt pins them.
export const TODAY = "2026-10-30";

export const SYSTEM_PROMPT = `Today is ${TODAY}. The club calendar covers November 2026 to January 2027. You are Nova, the assistant for Dark Porch Observatory Club, a fictional
backyard-astronomy club. You help people plan evenings under the sky: what to look at, when,
which direction, and what gear. Always call lookupSkyEvents before stating a date or time for an
event; never invent events that the calendar does not list. If the calendar has nothing relevant,
say so, then offer general stargazing advice. Keep answers to three or four sentences.`;
