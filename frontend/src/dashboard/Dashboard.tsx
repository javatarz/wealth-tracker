import { useState, type ReactNode } from "react";

import type {
  DashboardPosition,
  DashboardSummary,
  Scope,
} from "./dashboardApi";
import { ALL } from "./dashboardApi";
import { FilterBar } from "./FilterBar";
import { GrowthGraph } from "./GrowthGraph";
import { ReturnsSummary } from "./ReturnsSummary";
import { SummaryTable } from "./SummaryTable";
import { useDashboard, type DashboardState } from "./useDashboard";
import { useFilters } from "./useFilters";

type Kind = DashboardState["kind"];
type StateOf<K extends Kind> = Extract<DashboardState, { kind: K }>;

interface DashboardProps {
  onOpenPosition: (position: DashboardPosition) => void;
}

export function Dashboard({ onOpenPosition }: DashboardProps) {
  const filters = useFilters();
  const [scope, setScope] = useState<Scope>({ member: ALL, assetClass: ALL });
  const state = useDashboard(scope);

  return (
    <section aria-labelledby="dashboard-heading">
      <h2 id="dashboard-heading">Net Worth</h2>
      <FilterBar filters={filters} scope={scope} onChange={setScope} />
      {renderState(state.kind, state, onOpenPosition)}
    </section>
  );
}

const views: {
  [K in Kind]: (
    state: StateOf<K>,
    onOpenPosition: DashboardProps["onOpenPosition"],
  ) => ReactNode;
} = {
  loading: () => (
    <p role="status" className="muted">
      Loading your Net Worth…
    </p>
  ),
  error: ({ message }) => (
    <p role="alert" className="callout bad">
      {message}
    </p>
  ),
  ok: ({ dashboard }, onOpenPosition) => (
    <Loaded dashboard={dashboard} onOpenPosition={onOpenPosition} />
  ),
};

function renderState<K extends Kind>(
  kind: K,
  state: StateOf<K>,
  onOpenPosition: DashboardProps["onOpenPosition"],
): ReactNode {
  return views[kind](state, onOpenPosition);
}

function Loaded({
  dashboard,
  onOpenPosition,
}: {
  dashboard: DashboardSummary;
  onOpenPosition: DashboardProps["onOpenPosition"];
}) {
  return (
    <>
      <section aria-labelledby="growth-heading">
        <h3 id="growth-heading">Growth</h3>
        <GrowthGraph series={dashboard.series} />
        <p className="muted small">Configure benchmarks in Settings</p>
      </section>
      {dashboard.positions.length === 0 ? (
        <p className="muted" role="status">
          No Positions match this view.
        </p>
      ) : (
        <>
          <ReturnsSummary dashboard={dashboard} />
          <SummaryTable
            dashboard={dashboard}
            onSelectPosition={onOpenPosition}
          />
        </>
      )}
    </>
  );
}
