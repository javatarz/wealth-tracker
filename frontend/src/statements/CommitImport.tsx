import { MismatchCards } from "./MismatchCards";
import type { Upload } from "./upload";
import { useCommit } from "./useCommit";

interface CommitImportProps {
  upload: Upload;
  onCommitted: () => void;
}

export function CommitImport({ upload, onCommitted }: CommitImportProps) {
  const { status, mismatches, decisions, ready, commit, decide } = useCommit(
    upload,
    onCommitted,
  );

  return (
    <>
      {mismatches.length > 0 && (
        <MismatchCards
          mismatches={mismatches}
          decisions={decisions}
          onDecide={decide}
        />
      )}
      <div className="commit-bar">
        <button
          type="button"
          className="btn btn-primary"
          disabled={!ready}
          onClick={() => {
            void commit();
          }}
        >
          {status.kind === "committing" ? "Committing…" : "Commit import"}
        </button>
        {status.kind === "failed" && (
          <p role="alert" className="callout bad">
            {status.message}
          </p>
        )}
      </div>
    </>
  );
}
