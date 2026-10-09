import { DropZone } from "./DropZone";
import { ImportOutcome } from "./ImportOutcome";
import { useStatementImport } from "./useStatementImport";

export function StatementImport({ onCommitted }: { onCommitted: () => void }) {
  const { state, parse } = useStatementImport();

  return (
    <section aria-labelledby="import-heading">
      <h2 id="import-heading">Import a CAMS statement</h2>
      <DropZone
        disabled={state.kind === "parsing"}
        onFile={(file) => {
          void parse({ file, password: "" });
        }}
      />
      <ImportOutcome
        state={state}
        actions={{
          retry: (upload) => {
            void parse(upload);
          },
          committed: onCommitted,
        }}
      />
    </section>
  );
}
