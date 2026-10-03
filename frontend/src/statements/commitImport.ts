import { api } from "../api/client";
import type { components } from "../api/schema";
import { asForm, type Upload } from "./upload";

export type ImportReceipt = components["schemas"]["ImportReceipt"];

export type CommitResult =
  { kind: "ok"; receipt: ImportReceipt } | { kind: "error"; message: string };

type CommitResponse = Awaited<ReturnType<typeof commit>>;

const REJECTED = "The import was rejected by the server.";
const UNREACHABLE: CommitResult = {
  kind: "error",
  message: "Couldn't reach the Wealth Tracker server.",
};

export async function commitImport(statement: Upload): Promise<CommitResult> {
  try {
    return toResult(await commit(statement));
  } catch {
    return UNREACHABLE;
  }
}

function commit(statement: Upload) {
  return api.POST("/api/imports", asForm(statement));
}

function toResult({ data, error }: CommitResponse): CommitResult {
  return data
    ? { kind: "ok", receipt: data }
    : { kind: "error", message: messageOf(error) };
}

function messageOf(error: CommitResponse["error"]): string {
  return error && "message" in error ? error.message : REJECTED;
}
