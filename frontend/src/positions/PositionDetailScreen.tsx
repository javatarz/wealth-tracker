import { useEffect, useState, type ReactNode } from "react";

import { formatDecimal } from "../statements/formatDecimal";
import { AddTransactionForm } from "./AddTransactionForm";
import { IncomeSection } from "./IncomeSection";
import {
  getPosition,
  type DetailResult,
  type PositionDetail,
} from "./positionDetail";
import { TransactionList } from "./TransactionList";

type DetailState = { kind: "loading" } | DetailResult;
type Kind = DetailState["kind"];
type StateOf<K extends Kind> = Extract<DetailState, { kind: K }>;

export interface DetailActions {
  added: (position: PositionDetail) => void;
}

type View<K extends Kind> = (
  state: StateOf<K>,
  actions: DetailActions,
) => ReactNode;

const views: { [K in Kind]: View<K> } = {
  loading: () => (
    <p role="status" className="muted">
      Loading Position…
    </p>
  ),
  error: ({ message }) => (
    <p role="alert" className="callout bad">
      {message}
    </p>
  ),
  ok: ({ position }, { added }) => (
    <PositionBody position={position} onAdded={added} />
  ),
};

function renderView<K extends Kind>(
  kind: K,
  state: StateOf<K>,
  actions: DetailActions,
): ReactNode {
  return views[kind](state, actions);
}

export function PositionDetailScreen({
  positionId,
  onBack,
}: {
  positionId: string;
  onBack: () => void;
}) {
  const [state, setState] = useState<DetailState>({ kind: "loading" });

  useEffect(() => {
    void getPosition(positionId).then(setState);
  }, [positionId]);

  return (
    <section aria-labelledby="position-detail-heading">
      <button type="button" className="btn" onClick={onBack}>
        Back to Positions
      </button>
      <h2 id="position-detail-heading">{heading(state)}</h2>
      {renderView(state.kind, state, {
        added: (position) => {
          setState({ kind: "ok", position });
        },
      })}
    </section>
  );
}

function heading(state: DetailState): string {
  return state.kind === "ok" ? state.position.scheme : "Position detail";
}

function PositionBody({
  position,
  onAdded,
}: {
  position: PositionDetail;
  onAdded: (position: PositionDetail) => void;
}) {
  return (
    <>
      <p className="position-summary">
        {position.institution} · <span className="mono">{position.folio}</span>{" "}
        · Units {formatDecimal(position.units)} · Cost basis ₹
        {formatDecimal(position.cost_basis)}
      </p>
      <AddTransactionForm
        position={position}
        today={todayIso()}
        onAdded={onAdded}
      />
      <IncomeSection position={position} onRecorded={onAdded} />
      <h3>Transactions</h3>
      <TransactionList entries={position.transactions} />
    </>
  );
}

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}
