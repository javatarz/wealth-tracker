import { useEffect, useState } from "react";

import { getDashboard, type DashboardResult, type Scope } from "./dashboardApi";

export type DashboardState = { kind: "loading" } | DashboardResult;

export function useDashboard({ member, assetClass }: Scope): DashboardState {
  const [state, setState] = useState<DashboardState>({ kind: "loading" });

  useEffect(() => {
    void getDashboard({ member, assetClass }).then(setState);
  }, [member, assetClass]);

  return state;
}
