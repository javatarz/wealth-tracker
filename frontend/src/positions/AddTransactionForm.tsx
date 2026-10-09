import type { AddTransactionState } from "./addTransaction";
import type { PositionDetail } from "./positionDetail";
import { TransactionFields } from "./TransactionFields";
import { useManualEntry } from "./useManualEntry";

interface AddTransactionFormProps {
  position: PositionDetail;
  today: string;
  onAdded: (position: PositionDetail) => void;
}

export function AddTransactionForm({
  position,
  today,
  onAdded,
}: AddTransactionFormProps) {
  const entry = useManualEntry(position, today, onAdded);
  return (
    <form
      className="add-transaction"
      aria-labelledby="add-transaction-heading"
      onSubmit={(event) => {
        event.preventDefault();
        void entry.submit();
      }}
    >
      <h3 id="add-transaction-heading">Add Transaction</h3>
      <TransactionFields
        draft={{ ...entry.draft, type: entry.entryType }}
        allowedTypes={position.allowed_types}
        onChange={entry.edit}
      />
      <SubmitButton saving={entry.state.kind === "saving"} />
      <Failure state={entry.state} />
    </form>
  );
}

function SubmitButton({ saving }: { saving: boolean }) {
  return (
    <button type="submit" className="btn btn-primary" disabled={saving}>
      {saving ? "Saving…" : "Add Transaction"}
    </button>
  );
}

function Failure({ state }: { state: AddTransactionState }) {
  if (state.kind !== "invalid") {
    return null;
  }
  return (
    <p role="alert" className="callout bad">
      {state.message}
    </p>
  );
}
