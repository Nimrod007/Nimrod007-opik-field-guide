// The scripted customer questions the CLI plays.
export const SCRIPT: string[] = [
  // One tool: meter lookup.
  "What was the last electricity meter reading on account HL-20418?",
  // Usage history, expects the August water spike to be called out.
  "My bill for account HL-20418 looked high a couple of months ago. Can you look at the last 6 months of usage?",
  // Known outage: check only, no report filed.
  "The power is out at my place, account HL-31977. What's going on?",
  // Nothing published: check_known_outage then report_outage.
  "Water pressure dropped to nothing at account HL-20418 and the neighbours have the same problem. Please report it.",
];
