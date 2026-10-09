import type { ReactNode } from "react";

import { formatDecimal } from "../statements/formatDecimal";
import type { PositionSummary } from "./listPositions";
import { usePosition, type PositionState } from "./usePosition";
import { AppraisedValueForm } from "./AppraisedValueForm";
import {
  APPRAISED,
  type Appraisal,
  type AppraisalResult,
  type ValuationPoint,
} from "./valuation";

type Kind = PositionState["kind"];
type StateOf<K extends Kind> = Extract<PositionState, { kind: K }>;
type Appraise = (appraisal: Appraisal) => Promise<AppraisalResult>;
type View<K extends Kind> = (
  state: StateOf<K>,
  appraise: Appraise,
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
  ok: ({ position, history }, appraise) => (
    <PositionCard position={position} history={history} appraise={appraise} />
  ),
};

function renderView<K extends Kind>(
  kind: K,
  state: StateOf<K>,
  appraise: Appraise,
): ReactNode {
  return views[kind](state, appraise);
}

export function PositionDetail({
  id,
  onBack,
}: {
  id: string;
  onBack: () => void;
}) {
  const { state, appraise } = usePosition(id);

  return (
    <section aria-labelledby="position-heading">
      <button type="button" className="btn" onClick={onBack}>
        ← All Positions
      </button>
      {renderView(state.kind, state, appraise)}
    </section>
  );
}

interface CardProps {
  position: PositionSummary;
  history: ValuationPoint[];
  appraise: Appraise;
}

function PositionCard({ position, history, appraise }: CardProps) {
  return (
    <>
      <h2 id="position-heading">{position.scheme}</h2>
      <PositionMeta position={position} />
      <CurrentValue position={position} />
      {position.valuation_strategy === APPRAISED && (
        <AppraisedValueForm onSave={appraise} />
      )}
      <ValuationHistory history={history} />
    </>
  );
}

function PositionMeta({ position }: { position: PositionSummary }) {
  return (
    <dl className="scheme-meta">
      <Meta term="Account">
        {position.institution} · <span className="mono">{position.folio}</span>
      </Meta>
      <Meta term="Units">{formatDecimal(position.units)}</Meta>
      <Meta term="Cost basis">₹{formatDecimal(position.cost_basis)}</Meta>
      <Meta term="Valuation strategy">{position.valuation_label}</Meta>
    </dl>
  );
}

function Meta({ term, children }: { term: string; children: ReactNode }) {
  return (
    <div>
      <dt>{term}</dt>
      <dd>{children}</dd>
    </div>
  );
}

function CurrentValue({ position }: { position: PositionSummary }) {
  return (
    <div>
      <h3>Current value</h3>
      <p className="value">{formatDecimal(position.value)}</p>
      {position.warning !== null && (
        <p role="status" className="callout warn">
          {position.warning}
        </p>
      )}
      {position.stale && (
        <p role="status" className="callout warn">
          Market data is stale.
        </p>
      )}
    </div>
  );
}

function ValuationHistory({ history }: { history: ValuationPoint[] }) {
  return (
    <div>
      <h3>Valuation history</h3>
      <table>
        <thead>
          <tr>
            <th scope="col">Date</th>
            <th scope="col" className="num">
              Value (₹)
            </th>
            <th scope="col">Priced on</th>
          </tr>
        </thead>
        <tbody>
          {history.map((point) => (
            <HistoryRow key={point.date} point={point} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function HistoryRow({ point }: { point: ValuationPoint }) {
  return (
    <tr>
      <th scope="row">{point.date}</th>
      <td className="num">{formatDecimal(point.value)}</td>
      <td>{point.priced_on ?? "—"}</td>
    </tr>
  );
}
