import { useEffect, useState } from "react";

import { listPositions, type PositionsResult } from "./listPositions";

export type PositionsState = { kind: "loading" } | PositionsResult;

export function usePositions(): PositionsState {
  const [state, setState] = useState<PositionsState>({ kind: "loading" });

  useEffect(() => {
    void listPositions().then(setState);
  }, []);

  return state;
}
