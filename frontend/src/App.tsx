import { useState, type ReactNode } from "react";

import { HealthStatus } from "./HealthStatus";
import { PositionDetailScreen } from "./positions/PositionDetailScreen";
import { PositionsList } from "./positions/PositionsList";
import { StatementImport } from "./statements/StatementImport";

type View = "positions" | "import";

interface ScreenProps {
  openPosition: string | null;
  onOpen: (positionId: string | null) => void;
  onImport: () => void;
  onCommitted: () => void;
}

const LABELS: Record<View, string> = {
  positions: "Positions",
  import: "Import statement",
};

const screens: Record<View, (props: ScreenProps) => ReactNode> = {
  positions: ({ openPosition, onOpen, onImport }) =>
    openPosition === null ? (
      <PositionsList onImport={onImport} onOpen={onOpen} />
    ) : (
      <PositionDetailScreen
        positionId={openPosition}
        onBack={() => {
          onOpen(null);
        }}
      />
    ),
  import: ({ onCommitted }) => <StatementImport onCommitted={onCommitted} />,
};

export default function App() {
  const [view, setView] = useState<View>("positions");
  const [openPosition, setOpenPosition] = useState<string | null>(null);
  const show = (next: View) => () => {
    setOpenPosition(null);
    setView(next);
  };

  return (
    <main>
      <h1>Wealth Tracker</h1>
      <HealthStatus />
      <Sections active={view} onShow={show} />
      {screens[view]({
        openPosition,
        onOpen: setOpenPosition,
        onImport: show("import"),
        onCommitted: show("positions"),
      })}
    </main>
  );
}

function Sections({
  active,
  onShow,
}: {
  active: View;
  onShow: (view: View) => () => void;
}) {
  return (
    <nav aria-label="Sections" className="sections">
      {(Object.keys(LABELS) as View[]).map((target) => (
        <button
          key={target}
          type="button"
          className="btn"
          aria-current={target === active ? "page" : undefined}
          onClick={onShow(target)}
        >
          {LABELS[target]}
        </button>
      ))}
    </nav>
  );
}
