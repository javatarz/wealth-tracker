import { useCallback, useEffect, useState } from "react";

import {
  getPosition,
  recordAppraisal,
  type Appraisal,
  type PositionResult,
} from "./valuation";

export type PositionState = { kind: "loading" } | PositionResult;

export function usePosition(id: string) {
  const [state, setState] = useState<PositionState>({ kind: "loading" });
  const reload = useCallback(() => {
    void getPosition(id).then(setState);
  }, [id]);

  useEffect(reload, [reload]);

  const appraise = useCallback(
    async (appraisal: Appraisal) => {
      const result = await recordAppraisal(id, appraisal);
      if (result.kind === "ok") {
        reload();
      }
      return result;
    },
    [id, reload],
  );

  return { state, appraise };
}
