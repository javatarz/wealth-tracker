import { formatDecimal } from "../statements/formatDecimal";
import { incomeTypeLabel } from "./incomeTypes";
import type { IncomeEntry } from "./positionDetail";

export function IncomeList({ entries }: { entries: IncomeEntry[] }) {
  if (entries.length === 0) {
    return <p className="muted">No Income recorded yet.</p>;
  }
  return (
    <table>
      <thead>
        <tr>
          <th scope="col">Date</th>
          <th scope="col">Type</th>
          <th scope="col" className="num">
            Gross (₹)
          </th>
          <th scope="col" className="num">
            Tax (₹)
          </th>
          <th scope="col" className="num">
            Net (₹)
          </th>
          <th scope="col">Disposition</th>
        </tr>
      </thead>
      <tbody>
        {entries.map((entry) => (
          <IncomeRow key={rowKey(entry)} entry={entry} />
        ))}
      </tbody>
    </table>
  );
}

function IncomeRow({ entry }: { entry: IncomeEntry }) {
  return (
    <tr>
      <td>{entry.date}</td>
      <th scope="row">{incomeTypeLabel(entry.kind)}</th>
      <td className="num">{formatDecimal(entry.gross_amount)}</td>
      <td className="num">{formatDecimal(entry.tax_deducted)}</td>
      <td className="num">{formatDecimal(entry.net_amount)}</td>
      <td>{disposition(entry)}</td>
    </tr>
  );
}

function disposition(entry: IncomeEntry): string {
  if (entry.units === null) {
    return "Withdrawn";
  }
  return `Reinvested · ${formatDecimal(entry.units)} units`;
}

function rowKey(entry: IncomeEntry): string {
  return `${entry.date}-${entry.kind}-${entry.net_amount}`;
}
