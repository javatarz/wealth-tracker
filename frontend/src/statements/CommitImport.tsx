import { useState } from "react";

import { commitImport } from "./commitImport";
import type { Upload } from "./upload";

type CommitState =
  | { kind: "idle" }
  | { kind: "committing" }
  | { kind: "failed"; message: string };

interface CommitImportProps {
  upload: Upload;
  onCommitted: () => void;
}

export function CommitImport({ upload, onCommitted }: CommitImportProps) {
  const [state, setState] = useState<CommitState>({ kind: "idle" });
  const committing = state.kind === "committing";

  async function commit() {
    setState({ kind: "committing" });
    const result = await commitImport(upload);
    if (result.kind === "error") {
      setState({ kind: "failed", message: result.message });
      return;
    }
    onCommitted();
  }

  return (
    <div className="commit-bar">
      <button
        type="button"
        className="btn btn-primary"
        disabled={committing}
        onClick={() => {
          void commit();
        }}
      >
        {committing ? "Committing…" : "Commit import"}
      </button>
      {state.kind === "failed" && (
        <p role="alert" className="callout bad">
          {state.message}
        </p>
      )}
    </div>
  );
}
