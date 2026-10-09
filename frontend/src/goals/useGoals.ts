import { useCallback, useEffect, useState } from "react";

import { listGoals, type GoalsResult } from "./listGoals";

export type GoalsState = { kind: "loading" } | GoalsResult;

export function useGoals() {
  const [state, setState] = useState<GoalsState>({ kind: "loading" });
  const [revision, setRevision] = useState(0);

  useEffect(() => {
    void listGoals().then(setState);
  }, [revision]);

  const reload = useCallback(() => {
    setRevision((current) => current + 1);
  }, []);

  return { state, reload };
}
