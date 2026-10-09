import { IncomeFields } from "./IncomeFields";
import type { IncomeFormState } from "./incomeDraft";
import type { PositionDetail } from "./positionDetail";
import { useIncome } from "./useIncome";

export function AddIncomeForm({
  position,
  today,
  onRecorded,
}: {
  position: PositionDetail;
  today: string;
  onRecorded: (position: PositionDetail) => void;
}) {
  const entry = useIncome(position, today, onRecorded);
  return (
    <form
      className="add-income"
      aria-labelledby="add-income-heading"
      onSubmit={(event) => {
        event.preventDefault();
        void entry.submit();
      }}
    >
      <h3 id="add-income-heading">Add Income</h3>
      <IncomeFields
        draft={{ ...entry.draft, type: entry.incomeType }}
        allowedTypes={position.allowed_income_types}
        reinvestable={position.reinvestable}
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
      {saving ? "Saving…" : "Add Income"}
    </button>
  );
}

function Failure({ state }: { state: IncomeFormState }) {
  if (state.kind !== "invalid") {
    return null;
  }
  return (
    <p role="alert" className="callout bad">
      {state.message}
    </p>
  );
}
