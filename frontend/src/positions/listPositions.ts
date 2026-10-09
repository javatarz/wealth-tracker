import { api } from "../api/client";
import type { components } from "../api/schema";

export type PositionSummary = components["schemas"]["PositionSummary"];

export type PositionsResult =
  | { kind: "ok"; positions: PositionSummary[] }
  | { kind: "error"; message: string };

const FAILED: PositionsResult = {
  kind: "error",
  message: "Couldn't load your Positions.",
};
const UNREACHABLE: PositionsResult = {
  kind: "error",
  message: "Couldn't reach the Wealth Tracker server.",
};

export async function listPositions(): Promise<PositionsResult> {
  try {
    const { data } = await api.GET("/api/positions");
    return data ? { kind: "ok", positions: data } : FAILED;
  } catch {
    return UNREACHABLE;
  }
}
