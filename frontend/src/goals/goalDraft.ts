import type { GoalWrite } from "./goalCommands";
import type { GoalSummary } from "./listGoals";

export interface GoalDraft {
  name: string;
  targetAmount: string;
  targetDate: string;
  accountIds: string[];
  projectionStrategy: string;
  cagrRate: string;
  trailingWindowYears: string;
}

const BLANK: GoalDraft = {
  name: "",
  targetAmount: "",
  targetDate: "",
  accountIds: [],
  projectionStrategy: "",
  cagrRate: "",
  trailingWindowYears: "",
};

export function draftOf(goal?: GoalSummary): GoalDraft {
  return goal ? fromGoal(goal) : BLANK;
}

function fromGoal(goal: GoalSummary): GoalDraft {
  return {
    name: goal.name,
    targetAmount: goal.target_amount,
    targetDate: goal.target_date,
    accountIds: goal.account_ids,
    projectionStrategy: text(goal.projection_strategy),
    cagrRate: text(goal.cagr_rate),
    trailingWindowYears: text(goal.trailing_window_years),
  };
}

function text(value: string | number | null | undefined): string {
  return value === null || value === undefined ? "" : String(value);
}

export function toggle(selected: string[], accountId: string): string[] {
  return selected.includes(accountId)
    ? selected.filter((chosen) => chosen !== accountId)
    : [...selected, accountId];
}

// Only the chosen strategy's parameters are sent; omitting the rest clears them.
const STRATEGY_WRITES: Record<
  string,
  (draft: GoalDraft) => Partial<GoalWrite>
> = {
  cagr: (draft) => ({
    projection_strategy: "cagr",
    cagr_rate: draft.cagrRate,
    trailing_window_years: null,
  }),
  trailing_window: (draft) => ({
    projection_strategy: "trailing_window",
    cagr_rate: null,
    trailing_window_years: Number(draft.trailingWindowYears),
  }),
};

export function toWrite(draft: GoalDraft): GoalWrite {
  return {
    name: draft.name.trim(),
    target_amount: draft.targetAmount,
    target_date: draft.targetDate,
    account_ids: draft.accountIds,
    ...(STRATEGY_WRITES[draft.projectionStrategy]?.(draft) ?? {}),
  };
}
