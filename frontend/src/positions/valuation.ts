import { api } from "../api/client";
import type { components } from "../api/schema";
import type { PositionSummary } from "./listPositions";

export type ValuationPoint = components["schemas"]["ValuationPoint"];

/** The Instrument valuation_strategy for user-supplied revaluations (ADR 0016). */
export const APPRAISED = "appraised";

export type PositionResult =
  | { kind: "ok"; position: PositionSummary; history: ValuationPoint[] }
  | { kind: "error"; message: string };

export type AppraisalResult =
  { kind: "ok" } | { kind: "error"; message: string };

export interface Appraisal {
  date: string;
  value: string;
}

const FAILED = "Couldn't load this Position.";
const UNREACHABLE = "Couldn't reach the Wealth Tracker server.";
const APPRAISAL_FAILED = "Couldn't record that appraisal.";

export async function getPosition(id: string): Promise<PositionResult> {
  try {
    return toPositionResult(await fetchPosition(id));
  } catch {
    return { kind: "error", message: UNREACHABLE };
  }
}

export async function recordAppraisal(
  id: string,
  appraisal: Appraisal,
): Promise<AppraisalResult> {
  try {
    return toAppraisalResult(await postAppraisal(id, appraisal));
  } catch {
    return { kind: "error", message: UNREACHABLE };
  }
}

async function fetchPosition(id: string) {
  const path = { path: { position_id: id } };
  const [position, history] = await Promise.all([
    api.GET("/api/positions/{position_id}", { params: path }),
    api.GET("/api/positions/{position_id}/valuation-history", { params: path }),
  ]);
  return { position, history };
}

async function postAppraisal(id: string, appraisal: Appraisal) {
  const { response } = await api.POST(
    "/api/positions/{position_id}/appraisal",
    {
      params: { path: { position_id: id } },
      body: appraisal,
    },
  );
  return response;
}

function toPositionResult({
  position,
  history,
}: Awaited<ReturnType<typeof fetchPosition>>): PositionResult {
  if (!position.data || !history.data) {
    return { kind: "error", message: FAILED };
  }
  return { kind: "ok", position: position.data, history: history.data };
}

function toAppraisalResult(response: Response): AppraisalResult {
  return response.ok
    ? { kind: "ok" }
    : { kind: "error", message: APPRAISAL_FAILED };
}
