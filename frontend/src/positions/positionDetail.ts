import { api } from "../api/client";
import type { components } from "../api/schema";

export type PositionDetail = components["schemas"]["PositionDetail"];
export type LedgerEntry = components["schemas"]["LedgerEntry"];
export type ManualTransactionRequest =
  components["schemas"]["ManualTransactionRequest"];

export type DetailResult =
  { kind: "ok"; position: PositionDetail } | { kind: "error"; message: string };

type DetailResponse = Awaited<ReturnType<typeof findPosition>>;
type AddResponse = Awaited<ReturnType<typeof postTransaction>>;

const REJECTED = "The server rejected that Position request.";
const UNREACHABLE: DetailResult = {
  kind: "error",
  message: "Couldn't reach the Wealth Tracker server.",
};

export async function getPosition(positionId: string): Promise<DetailResult> {
  try {
    return toResult(await findPosition(positionId));
  } catch {
    return UNREACHABLE;
  }
}

export async function addTransaction(
  positionId: string,
  request: ManualTransactionRequest,
): Promise<DetailResult> {
  try {
    return toResult(await postTransaction(positionId, request));
  } catch {
    return UNREACHABLE;
  }
}

function findPosition(positionId: string) {
  return api.GET("/api/positions/{position_id}", {
    params: { path: { position_id: positionId } },
  });
}

function postTransaction(
  positionId: string,
  request: ManualTransactionRequest,
) {
  return api.POST("/api/positions/{position_id}/transactions", {
    params: { path: { position_id: positionId } },
    body: request,
  });
}

function toResult({ data, error }: DetailResponse | AddResponse): DetailResult {
  return data
    ? { kind: "ok", position: data }
    : { kind: "error", message: messageOf(error) };
}

function messageOf(error: DetailResponse["error"]): string {
  return error && "message" in error ? error.message : REJECTED;
}
