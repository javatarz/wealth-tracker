import type { ReactNode } from "react";

import { formatDecimal } from "../statements/formatDecimal";
import type { PositionSummary } from "./listPositions";
import { usePositions, type PositionsState } from "./usePositions";

type Kind = PositionsState["kind"];
type StateOf<K extends Kind> = Extract<PositionsState, { kind: K }>;
type View<K extends Kind> = (
  state: StateOf<K>,
  onImport: () => void,
) => ReactNode;

const views: { [K in Kind]: View<K> } = {
  loading: () => (
    <p role="status" className="muted">
      Loading Positions…
    </p>
  ),
  error: ({ message }) => (
    <p role="alert" className="callout bad">
      {message}
    </p>
  ),
  ok: ({ positions }, onImport) =>
    positions.length === 0 ? (
      <NoPositions onImport={onImport} />
    ) : (
      <PositionsTable positions={positions} />
    ),
};

function renderView<K extends Kind>(
  kind: K,
  state: StateOf<K>,
  onImport: () => void,
): ReactNode {
  return views[kind](state, onImport);
}

export function PositionsList({ onImport }: { onImport: () => void }) {
  const state = usePositions();

  return (
    <section aria-labelledby="positions-heading">
      <h2 id="positions-heading">Positions</h2>
      {renderView(state.kind, state, onImport)}
    </section>
  );
}

function NoPositions({ onImport }: { onImport: () => void }) {
  return (
    <p className="muted">
      No Positions yet.{" "}
      <button type="button" className="btn" onClick={onImport}>
        Import a statement
      </button>
    </p>
  );
}

function PositionsTable({ positions }: { positions: PositionSummary[] }) {
  return (
    <table>
      <thead>
        <tr>
          <th scope="col">Scheme</th>
          <th scope="col">Account</th>
          <th scope="col" className="num">
            Units
          </th>
          <th scope="col" className="num">
            Cost basis (₹)
          </th>
        </tr>
      </thead>
      <tbody>
        {positions.map((position) => (
          <PositionRow key={position.id} position={position} />
        ))}
      </tbody>
    </table>
  );
}

function PositionRow({ position }: { position: PositionSummary }) {
  return (
    <tr>
      <th scope="row">{position.scheme}</th>
      <td>
        {position.institution} · <span className="mono">{position.folio}</span>
      </td>
      <td className="num">{formatDecimal(position.units)}</td>
      <td className="num">{formatDecimal(position.cost_basis)}</td>
    </tr>
  );
}
