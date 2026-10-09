import { api } from "../api/client";
import type { components } from "../api/schema";

export type GoalSummary = components["schemas"]["GoalSummary"];
export type AccountSummary = components["schemas"]["AccountSummary"];

export type GoalsResult =
  | { kind: "ok"; goals: GoalSummary[]; accounts: AccountSummary[] }
  | { kind: "error"; message: string };

const FAILED: GoalsResult = {
  kind: "error",
  message: "Couldn't load your Goals.",
};
const UNREACHABLE: GoalsResult = {
  kind: "error",
  message: "Couldn't reach the Wealth Tracker server.",
};

export async function listGoals(): Promise<GoalsResult> {
  try {
    const [goals, accounts] = await Promise.all([
      api.GET("/api/goals"),
      api.GET("/api/accounts"),
    ]);
    return combine(goals.data, accounts.data);
  } catch {
    return UNREACHABLE;
  }
}

function combine(
  goals: GoalSummary[] | undefined,
  accounts: AccountSummary[] | undefined,
): GoalsResult {
  return goals && accounts ? { kind: "ok", goals, accounts } : FAILED;
}
