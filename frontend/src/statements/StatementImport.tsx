import { DropZone } from "./DropZone";
import { ImportOutcome } from "./ImportOutcome";
import { useStatementImport } from "./useStatementImport";

export function StatementImport() {
  const { state, parse } = useStatementImport();

  return (
    <section aria-labelledby="import-heading">
      <h2 id="import-heading">Preview a CAMS statement</h2>
      <DropZone
        disabled={state.kind === "parsing"}
        onFile={(file) => {
          void parse(file);
        }}
      />
      <ImportOutcome
        state={state}
        retry={(file, password) => {
          void parse(file, password);
        }}
      />
    </section>
  );
}
