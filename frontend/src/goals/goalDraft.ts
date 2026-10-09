import type { GoalWrite } from "./goalCommands";
import type { GoalSummary } from "./listGoals";

export interface GoalDraft {
  name: string;
  targetAmount: string;
  targetDate: string;
  accountIds: string[];
}

const BLANK: GoalDraft = {
  name: "",
  targetAmount: "",
  targetDate: "",
  accountIds: [],
};

export function draftOf(goal?: GoalSummary): GoalDraft {
  return goal
    ? {
        name: goal.name,
        targetAmount: goal.target_amount,
        targetDate: goal.target_date,
        accountIds: goal.account_ids,
      }
    : BLANK;
}

export function toggle(selected: string[], accountId: string): string[] {
  return selected.includes(accountId)
    ? selected.filter((chosen) => chosen !== accountId)
    : [...selected, accountId];
}

export function toWrite(draft: GoalDraft): GoalWrite {
  return {
    name: draft.name.trim(),
    target_amount: draft.targetAmount,
    target_date: draft.targetDate,
    account_ids: draft.accountIds,
  };
}
