export type AddTransactionState =
  { kind: "idle" } | { kind: "saving" } | { kind: "invalid"; message: string };

export interface Draft {
  type: string;
  date: string;
  units: string;
  amount: string;
  notes: string;
}

export const EMPTY_DRAFT: Draft = {
  type: "",
  date: "",
  units: "",
  amount: "",
  notes: "",
};

const REQUIRED = "Fill in the Transaction type, date and units.";
const FUTURE = "A Transaction can't be dated in the future.";
const UNIT_RANGE = "Units must be greater than zero.";
const COST_RANGE = "Cost can't be negative.";

type Rule = (draft: Draft, today: string) => string | null;

// Each rule owns one mistake, so adding a check never touches the others.
const rules: Rule[] = [
  (draft) =>
    draft.type === "" || draft.date === "" || draft.units === ""
      ? REQUIRED
      : null,
  (draft, today) => (draft.date > today ? FUTURE : null),
  (draft) => (Number(draft.units) > 0 ? null : UNIT_RANGE),
  (draft) =>
    draft.amount === "" || Number(draft.amount) >= 0 ? null : COST_RANGE,
];

/** Validates the form the same way the server does, so obvious mistakes never leave the browser. */
export function draftError(draft: Draft, today: string): string | null {
  return (
    rules
      .map((rule) => rule(draft, today))
      .find((message) => message !== null) ?? null
  );
}
