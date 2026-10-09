import { useState } from "react";

import { stateAfter, type ImportState } from "./importState";
import { previewStatement } from "./previewStatement";
import type { Upload } from "./upload";

export function useStatementImport() {
  const [state, setState] = useState<ImportState>({ kind: "idle" });

  async function parse(upload: Upload) {
    setState({ kind: "parsing", upload });
    setState(stateAfter(upload, await previewStatement(upload)));
  }

  return { state, parse };
}
