import type { ReactNode } from "react";

import { formatDecimal } from "../statements/formatDecimal";
import type { PositionSummary } from "./listPositions";
import { usePositions, type PositionsState } from "./usePositions";

type Kind = PositionsState["kind"];
type StateOf<K extends Kind> = Extract<PositionsState, { kind: K }>;
type View<K extends Kind> = (
  state: StateOf<K>,
  actions: ListActions,
) => ReactNode;

export interface ListActions {
  import: () => void;
  open: (positionId: string) => void;
}

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
  ok: ({ positions }, actions) =>
    positions.length === 0 ? (
      <NoPositions onImport={actions.import} />
    ) : (
      <PositionsTable positions={positions} onOpen={actions.open} />
    ),
};

function renderView<K extends Kind>(
  kind: K,
  state: StateOf<K>,
  actions: ListActions,
): ReactNode {
  return views[kind](state, actions);
}

export function PositionsList({
  onImport,
  onOpen,
}: {
  onImport: () => void;
  onOpen: (positionId: string) => void;
}) {
  const state = usePositions();

  return (
    <section aria-labelledby="positions-heading">
      <h2 id="positions-heading">Positions</h2>
      {renderView(state.kind, state, { import: onImport, open: onOpen })}
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

function PositionsTable({
  positions,
  onOpen,
}: {
  positions: PositionSummary[];
  onOpen: (positionId: string) => void;
}) {
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
          <th scope="col">
            <span className="visually-hidden">Actions</span>
          </th>
        </tr>
      </thead>
      <tbody>
        {positions.map((position) => (
          <PositionRow key={position.id} position={position} onOpen={onOpen} />
        ))}
      </tbody>
    </table>
  );
}

function PositionRow({
  position,
  onOpen,
}: {
  position: PositionSummary;
  onOpen: (positionId: string) => void;
}) {
  return (
    <tr>
      <th scope="row">{position.scheme}</th>
      <td>
        {position.institution} · <span className="mono">{position.folio}</span>
      </td>
      <td className="num">{formatDecimal(position.units)}</td>
      <td className="num">{formatDecimal(position.cost_basis)}</td>
      <td>
        <button
          type="button"
          className="btn"
          onClick={() => {
            onOpen(position.id);
          }}
        >
          Open <span className="visually-hidden">{position.scheme}</span>
        </button>
      </td>
    </tr>
  );
}
