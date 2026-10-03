import { api } from "../api/client";
import type { components } from "../api/schema";
import {
  decisionFields,
  type Decisions,
  type Mismatch,
} from "./reconciliation";
import { asForm, type Upload } from "./upload";

type Outcome =
  | components["schemas"]["ImportReceipt"]
  | components["schemas"]["DecisionsRequired"];

export type CommitResult =
  | { kind: "committed" }
  | { kind: "needsDecisions"; mismatches: Mismatch[] }
  | { kind: "error"; message: string };

type CommitResponse = Awaited<ReturnType<typeof commit>>;

const REJECTED = "The import was rejected by the server.";
const UNREACHABLE: CommitResult = {
  kind: "error",
  message: "Couldn't reach the Wealth Tracker server.",
};

export async function commitImport(
  statement: Upload,
  decisions: Decisions,
): Promise<CommitResult> {
  try {
    return toResult(await commit(statement, decisions));
  } catch {
    return UNREACHABLE;
  }
}

function commit(statement: Upload, decisions: Decisions) {
  return api.POST("/api/imports", asForm(statement, decisionFields(decisions)));
}

function toResult({ data, error }: CommitResponse): CommitResult {
  return data
    ? fromOutcome(data)
    : { kind: "error", message: messageOf(error) };
}

function fromOutcome(outcome: Outcome): CommitResult {
  return outcome.outcome === "committed"
    ? { kind: "committed" }
    : { kind: "needsDecisions", mismatches: outcome.mismatches };
}

function messageOf(error: CommitResponse["error"]): string {
  return error && "message" in error ? error.message : REJECTED;
}
