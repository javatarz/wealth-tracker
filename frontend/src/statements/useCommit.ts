import { useState } from "react";

import { commitImport, type CommitResult } from "./commitImport";
import {
  resolvedCount,
  type Action,
  type Decisions,
  type Mismatch,
} from "./reconciliation";
import type { Upload } from "./upload";

export type CommitStatus =
  | { kind: "idle" }
  | { kind: "committing" }
  | { kind: "failed"; message: string };

type Kind = CommitResult["kind"];
type ResultOf<K extends Kind> = Extract<CommitResult, { kind: K }>;
type Handlers = { [K in Kind]: (result: ResultOf<K>) => void };

function handle<K extends Kind>(
  kind: K,
  result: ResultOf<K>,
  handlers: Handlers,
) {
  handlers[kind](result);
}

/** Commits an Upload, collecting a decision for every mismatch the server reports. */
export function useCommit(upload: Upload, onCommitted: () => void) {
  const [status, setStatus] = useState<CommitStatus>({ kind: "idle" });
  const [mismatches, setMismatches] = useState<Mismatch[]>([]);
  const [decisions, setDecisions] = useState<Decisions>({});

  const handlers: Handlers = {
    committed: onCommitted,
    needsDecisions: (result) => {
      setMismatches(result.mismatches);
      setStatus({ kind: "idle" });
    },
    error: ({ message }) => {
      setStatus({ kind: "failed", message });
    },
  };

  async function commit() {
    setStatus({ kind: "committing" });
    const result = await commitImport(upload, decisions);
    handle(result.kind, result, handlers);
  }

  function decide(holding: string, action: Action) {
    setDecisions((chosen) => ({ ...chosen, [holding]: action }));
  }

  const undecided = mismatches.length - resolvedCount(mismatches, decisions);
  const ready = status.kind !== "committing" && undecided === 0;
  return { status, mismatches, decisions, ready, commit, decide };
}
