import type { components } from "../api/schema";

export type Mismatch = components["schemas"]["Mismatch"];

/** How a mismatch between printed and derived units is resolved (ADR 0027). */
export type Action = "trust_ledger" | "trust_statement" | "leave_out";

/** The chosen Action for each mismatch, keyed by its holding. */
export type Decisions = Record<string, Action>;

export const ACTIONS: { action: Action; label: string }[] = [
  { action: "trust_ledger", label: "Trust our ledger" },
  { action: "trust_statement", label: "Trust the statement" },
  { action: "leave_out", label: "Leave this scheme out" },
];

export function resolvedCount(mismatches: Mismatch[], decisions: Decisions) {
  return mismatches.filter(({ holding }) => holding in decisions).length;
}

/** Only sends decisions once there are some, so a clean commit stays a plain upload. */
export function decisionFields(decisions: Decisions): Record<string, string> {
  return Object.keys(decisions).length > 0
    ? { decisions: JSON.stringify(decisions) }
    : {};
}
