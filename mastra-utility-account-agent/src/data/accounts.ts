// Fictional records for "Harborlight Utilities". Everything is in memory so the
// only thing that leaves your machine is the model call.

export interface Account {
  accountId: string;
  holder: string;
  address: string;
  serviceZone: string;
  meters: { electricity: string; water: string };
}

export interface MeterReading {
  meterId: string;
  kind: "electricity" | "water";
  unit: "kWh" | "m3";
  reading: number;
  readAt: string; // ISO date
}

export interface MonthlyUsage {
  month: string; // YYYY-MM
  electricityKwh: number;
  waterM3: number;
  billUsd: number;
}

export interface Outage {
  zone: string;
  kind: "electricity" | "water";
  startedAt: string;
  restoreEta: string;
  cause: string;
}

export const ACCOUNTS: Record<string, Account> = {
  "HL-20418": {
    accountId: "HL-20418",
    holder: "Mira Okonkwo",
    address: "14 Larkspur Row",
    serviceZone: "north-bay",
    meters: { electricity: "E-77120", water: "W-30455" },
  },
  "HL-31977": {
    accountId: "HL-31977",
    holder: "Dev Anand Patel",
    address: "9 Quarry Lane",
    serviceZone: "east-ridge",
    meters: { electricity: "E-77988", water: "W-30901" },
  },
};

export const READINGS: Record<string, MeterReading> = {
  "E-77120": { meterId: "E-77120", kind: "electricity", unit: "kWh", reading: 48213, readAt: "2026-10-01" },
  "W-30455": { meterId: "W-30455", kind: "water", unit: "m3", reading: 1392.4, readAt: "2026-10-01" },
  "E-77988": { meterId: "E-77988", kind: "electricity", unit: "kWh", reading: 90544, readAt: "2026-10-02" },
  "W-30901": { meterId: "W-30901", kind: "water", unit: "m3", reading: 2210.9, readAt: "2026-10-02" },
};

// Six months of history, oldest first. HL-20418 has a water spike in 2026-08
// (a leak, say) that the agent should be able to point out.
export const USAGE: Record<string, MonthlyUsage[]> = {
  "HL-20418": [
    { month: "2026-05", electricityKwh: 310, waterM3: 11, billUsd: 78.4 },
    { month: "2026-06", electricityKwh: 355, waterM3: 12, billUsd: 86.9 },
    { month: "2026-07", electricityKwh: 420, waterM3: 12, billUsd: 99.2 },
    { month: "2026-08", electricityKwh: 438, waterM3: 31, billUsd: 141.7 },
    { month: "2026-09", electricityKwh: 372, waterM3: 13, billUsd: 90.1 },
    { month: "2026-10", electricityKwh: 301, waterM3: 11, billUsd: 76.0 },
  ],
  "HL-31977": [
    { month: "2026-05", electricityKwh: 540, waterM3: 18, billUsd: 128.3 },
    { month: "2026-06", electricityKwh: 575, waterM3: 19, billUsd: 135.0 },
    { month: "2026-07", electricityKwh: 690, waterM3: 21, billUsd: 158.8 },
    { month: "2026-08", electricityKwh: 702, waterM3: 20, billUsd: 160.1 },
    { month: "2026-09", electricityKwh: 610, waterM3: 19, billUsd: 141.5 },
    { month: "2026-10", electricityKwh: 512, waterM3: 18, billUsd: 121.9 },
  ],
};

// Known outages the utility already publishes; zones not listed are clear.
export const KNOWN_OUTAGES: Outage[] = [
  {
    zone: "east-ridge",
    kind: "electricity",
    startedAt: "2026-10-13T06:40",
    restoreEta: "2026-10-13T16:00",
    cause: "Substation transformer replacement",
  },
];

// Outage reports filed this session land here (see tools/outage.ts).
export const FILED_REPORTS: { ticketId: string; accountId: string; kind: string; details: string }[] = [];
