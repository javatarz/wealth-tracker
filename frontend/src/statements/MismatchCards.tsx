import { formatDecimal } from "./formatDecimal";
import {
  ACTIONS,
  resolvedCount,
  type Action,
  type Decisions,
  type Mismatch,
} from "./reconciliation";

interface MismatchCardsProps {
  mismatches: Mismatch[];
  decisions: Decisions;
  onDecide: (holding: string, action: Action) => void;
}

function signed(delta: string) {
  return `${delta.startsWith("-") ? "" : "+"}${formatDecimal(delta)}`;
}

function ActionChoice({
  chosen,
  onChoose,
}: {
  chosen: Action | undefined;
  onChoose: (action: Action) => void;
}) {
  return (
    <div role="group" aria-label="Resolve" className="mismatch-actions">
      {ACTIONS.map(({ action, label }) => (
        <button
          key={action}
          type="button"
          className="btn"
          aria-pressed={chosen === action}
          onClick={() => {
            onChoose(action);
          }}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

function MismatchCard({
  mismatch,
  chosen,
  onChoose,
}: {
  mismatch: Mismatch;
  chosen: Action | undefined;
  onChoose: (action: Action) => void;
}) {
  return (
    <article className="scheme mismatch" aria-label={mismatch.scheme}>
      <h4>{mismatch.scheme}</h4>
      <p className="muted">
        {mismatch.institution} · {mismatch.folio}
      </p>
      <dl className="mismatch-units">
        <dt>Statement says</dt>
        <dd>{formatDecimal(mismatch.printed_units)}</dd>
        <dt>Ledger says</dt>
        <dd>{formatDecimal(mismatch.derived_units)}</dd>
        <dt>Difference</dt>
        <dd>{signed(mismatch.delta)}</dd>
      </dl>
      <ActionChoice chosen={chosen} onChoose={onChoose} />
    </article>
  );
}

export function MismatchCards({
  mismatches,
  decisions,
  onDecide,
}: MismatchCardsProps) {
  const resolved = resolvedCount(mismatches, decisions);
  return (
    <section aria-labelledby="mismatch-heading" className="mismatches">
      <h3 id="mismatch-heading">Closing units don&apos;t match the ledger</h3>
      <p className="callout warn">
        Choose how to resolve each scheme before committing. Nothing is saved
        yet.
      </p>
      <p role="status">
        <progress value={resolved} max={mismatches.length} /> {resolved} of{" "}
        {mismatches.length} mismatches resolved
      </p>
      {mismatches.map((mismatch) => (
        <MismatchCard
          key={mismatch.holding}
          mismatch={mismatch}
          chosen={decisions[mismatch.holding]}
          onChoose={(action) => {
            onDecide(mismatch.holding, action);
          }}
        />
      ))}
    </section>
  );
}
