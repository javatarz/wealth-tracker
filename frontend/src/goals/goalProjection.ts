import { api } from "../api/client";
import type { components } from "../api/schema";

export type ProjectionView = components["schemas"]["ProjectionView"];

export type ProjectionResult =
  | { kind: "ok"; projection: ProjectionView }
  | { kind: "error"; message: string };

const FAILED: ProjectionResult = {
  kind: "error",
  message: "Couldn't load this Goal's projection.",
};
const UNREACHABLE: ProjectionResult = {
  kind: "error",
  message: "Couldn't reach the Wealth Tracker server.",
};

export async function loadProjection(
  goalId: string,
): Promise<ProjectionResult> {
  try {
    const { data } = await api.GET("/api/goals/{goal_id}/projection", {
      params: { path: { goal_id: goalId } },
    });
    return data ? { kind: "ok", projection: data } : FAILED;
  } catch {
    return UNREACHABLE;
  }
}
