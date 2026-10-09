import { formatDecimal } from "../statements/formatDecimal";
import { AddIncomeForm } from "./AddIncomeForm";
import { IncomeList } from "./IncomeList";
import type { PositionDetail } from "./positionDetail";

export function IncomeSection({
  position,
  onRecorded,
}: {
  position: PositionDetail;
  onRecorded: (position: PositionDetail) => void;
}) {
  return (
    <section aria-labelledby="income-heading">
      <h3 id="income-heading">Income</h3>
      <dl className="income-breakdown">
        <div>
          <dt>Total Income (net)</dt>
          <dd>₹{formatDecimal(position.income_total)}</dd>
        </div>
        <div>
          <dt>Withdrawn (Cash Flow)</dt>
          <dd>₹{formatDecimal(position.cash_flow_total)}</dd>
        </div>
      </dl>
      <AddIncomeForm
        position={position}
        today={todayIso()}
        onRecorded={onRecorded}
      />
      <IncomeList entries={position.income} />
    </section>
  );
}

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}
