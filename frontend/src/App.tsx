import { useState, type ReactNode } from "react";

import { HealthStatus } from "./HealthStatus";
import { PositionsList } from "./positions/PositionsList";
import { StatementImport } from "./statements/StatementImport";

type View = "positions" | "import";

const LABELS: Record<View, string> = {
  positions: "Positions",
  import: "Import statement",
};

export default function App() {
  const [view, setView] = useState<View>("positions");
  const show = (next: View) => () => {
    setView(next);
  };

  const screens: Record<View, ReactNode> = {
    positions: <PositionsList onImport={show("import")} />,
    import: <StatementImport onCommitted={show("positions")} />,
  };

  return (
    <main>
      <h1>Wealth Tracker</h1>
      <HealthStatus />
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
      {screens[view]}
    </main>
  );
}
