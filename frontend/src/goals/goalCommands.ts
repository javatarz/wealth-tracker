import { api } from "../api/client";
import type { components } from "../api/schema";

export type GoalWrite = components["schemas"]["GoalWrite"];

export type CommandResult = { kind: "ok" } | { kind: "error"; message: string };

const REJECTED = "The server rejected that Goal.";
const UNREACHABLE = "Couldn't reach the Wealth Tracker server.";

export async function createGoal(body: GoalWrite): Promise<CommandResult> {
  return run(() => api.POST("/api/goals", { body }), REJECTED);
}

export async function updateGoal(
  goalId: string,
  body: GoalWrite,
): Promise<CommandResult> {
  return run(
    () =>
      api.PUT("/api/goals/{goal_id}", {
        params: { path: { goal_id: goalId } },
        body,
      }),
    REJECTED,
  );
}

export async function deleteGoal(goalId: string): Promise<CommandResult> {
  return run(
    () =>
      api.DELETE("/api/goals/{goal_id}", {
        params: { path: { goal_id: goalId } },
      }),
    REJECTED,
  );
}

async function run(
  send: () => Promise<{ error?: unknown }>,
  fallback: string,
): Promise<CommandResult> {
  try {
    const { error } = await send();
    return error
      ? { kind: "error", message: messageOf(error, fallback) }
      : { kind: "ok" };
  } catch {
    return { kind: "error", message: UNREACHABLE };
  }
}

function messageOf(error: unknown, fallback: string): string {
  return isRejection(error) ? error.message : fallback;
}

function isRejection(error: unknown): error is { message: string } {
  return typeof error === "object" && error !== null && "message" in error;
}
