export type IncomeFormState =
  { kind: "idle" } | { kind: "saving" } | { kind: "invalid"; message: string };

export type Disposition = "reinvested" | "withdrawn";

export interface IncomeDraft {
  type: string;
  date: string;
  amount: string;
  tax: string;
  disposition: Disposition;
  nav: string;
}

export const EMPTY_INCOME_DRAFT: IncomeDraft = {
  type: "",
  date: "",
  amount: "",
  tax: "",
  disposition: "withdrawn",
  nav: "",
};

const REQUIRED = "Fill in the Income type, date and amount.";
const FUTURE = "Income can't be dated in the future.";
const AMOUNT_RANGE = "Gross amount must be greater than zero.";
const TAX_RANGE = "Tax can't be negative or more than the gross amount.";
const NAV_REQUIRED = "A reinvestment needs the NAV it bought at.";
const NAV_RANGE = "NAV must be greater than zero.";

type Rule = (draft: IncomeDraft, today: string) => string | null;

function reinvestmentError(draft: IncomeDraft): string | null {
  const checks: Record<Disposition, () => string | null> = {
    withdrawn: () => null,
    reinvested: () => navError(draft.nav),
  };
  return checks[draft.disposition]();
}

function navError(nav: string): string | null {
  if (Number(nav) > 0) {
    return null;
  }
  const empty: Partial<Record<string, string>> = { "": NAV_REQUIRED };
  return empty[nav] ?? NAV_RANGE;
}

// Each rule owns one mistake, so adding a check never touches the others.
const rules: Rule[] = [
  (draft) =>
    draft.type === "" || draft.date === "" || draft.amount === ""
      ? REQUIRED
      : null,
  (draft, today) => (draft.date > today ? FUTURE : null),
  (draft) => (Number(draft.amount) > 0 ? null : AMOUNT_RANGE),
  (draft) =>
    draft.tax === "" || Number(draft.tax) < Number(draft.amount)
      ? null
      : TAX_RANGE,
  (draft) => reinvestmentError(draft),
];

/** Validates the form the same way the server does, so obvious mistakes never leave the browser. */
export function incomeDraftError(
  draft: IncomeDraft,
  today: string,
): string | null {
  return (
    rules
      .map((rule) => rule(draft, today))
      .find((message) => message !== null) ?? null
  );
}
