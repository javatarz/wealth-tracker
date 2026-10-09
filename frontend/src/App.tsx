import { useState, type ReactNode } from "react";

import { Dashboard } from "./dashboard/Dashboard";
import type { DashboardPosition } from "./dashboard/dashboardApi";
import { Goals } from "./dashboard/Goals";
import { PositionDetail } from "./dashboard/PositionDetail";
import { HealthStatus } from "./HealthStatus";
import { PositionsList } from "./positions/PositionsList";
import { StatementImport } from "./statements/StatementImport";

type View = "dashboard" | "positions" | "goals" | "import";

const LABELS: Record<View, string> = {
  dashboard: "Net Worth",
  positions: "Positions",
  goals: "Goals",
  import: "Import statement",
};

export default function App() {
  const [view, setView] = useState<View>("dashboard");
  const [position, setPosition] = useState<DashboardPosition | null>(null);

  const show = (next: View) => () => {
    setPosition(null);
    setView(next);
  };

  const screens: Record<View, ReactNode> = {
    dashboard: <Dashboard onOpenPosition={setPosition} />,
    positions: <PositionsList onImport={show("import")} />,
    goals: <Goals />,
    import: <StatementImport onCommitted={show("positions")} />,
  };

  return (
    <main>
      <h1>Wealth Tracker</h1>
      <HealthStatus />
      <Nav view={view} show={show} />
      <Current
        view={view}
        position={position}
        screens={screens}
        onClose={show(view)}
      />
    </main>
  );
}

function Nav({ view, show }: { view: View; show: (view: View) => () => void }) {
  return (
    <nav aria-label="Sections" className="sections">
      {(Object.keys(LABELS) as View[]).map((target) => (
        <button
          key={target}
          type="button"
          className="btn"
          aria-current={target === view ? "page" : undefined}
          onClick={show(target)}
        >
          {LABELS[target]}
        </button>
      ))}
    </nav>
  );
}

function Current({
  view,
  position,
  screens,
  onClose,
}: {
  view: View;
  position: DashboardPosition | null;
  screens: Record<View, ReactNode>;
  onClose: () => void;
}) {
  if (position === null) {
    return screens[view];
  }
  return <PositionDetail position={position} onBack={onClose} />;
}
