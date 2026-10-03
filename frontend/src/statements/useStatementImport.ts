import { useState } from "react";

import { stateAfter, type ImportState } from "./importState";
import { previewStatement } from "./previewStatement";

export function useStatementImport() {
  const [state, setState] = useState<ImportState>({ kind: "idle" });

  async function parse(file: File, password = "") {
    setState({ kind: "parsing", file });
    setState(stateAfter(file, await previewStatement(file, password)));
  }

  return { state, parse };
}
