import { useState, type ReactNode } from "react";

import { HealthStatus } from "./HealthStatus";
import { PositionDetail } from "./positions/PositionDetail";
import { PositionsList } from "./positions/PositionsList";
import { StatementImport } from "./statements/StatementImport";

type View = "positions" | "import";

const LABELS: Record<View, string> = {
  positions: "Positions",
  import: "Import statement",
};

export default function App() {
  const [view, setView] = useState<View>("positions");
  const [detail, setDetail] = useState<string | null>(null);
  const show = (next: View) => () => {
    setDetail(null);
    setView(next);
  };
  const open = (id: string) => () => {
    setDetail(id);
  };
  const screens: Record<View, ReactNode> = {
    positions:
      detail === null ? (
        <PositionsList onImport={show("import")} onOpen={open} />
      ) : (
        <PositionDetail
          id={detail}
          onBack={() => {
            setDetail(null);
          }}
        />
      ),
    import: <StatementImport onCommitted={show("positions")} />,
  };

  return (
    <main>
      <h1>Wealth Tracker</h1>
      <HealthStatus />
      <SectionNav view={view} show={show} />
      {screens[view]}
    </main>
  );
}

function SectionNav({
  view,
  show,
}: {
  view: View;
  show: (next: View) => () => void;
}) {
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
