import { formatDecimal } from "../statements/formatDecimal";
import type { LedgerEntry } from "./positionDetail";
import { transactionTypeLabel } from "./transactionTypes";

export function TransactionList({ entries }: { entries: LedgerEntry[] }) {
  if (entries.length === 0) {
    return <p className="muted">No Transactions yet.</p>;
  }
  return (
    <table>
      <thead>
        <tr>
          <th scope="col">Date</th>
          <th scope="col">Type</th>
          <th scope="col" className="num">
            Units
          </th>
          <th scope="col" className="num">
            Cost (₹)
          </th>
          <th scope="col">Notes</th>
        </tr>
      </thead>
      <tbody>
        {entries.map((entry) => (
          <TransactionRow key={rowKey(entry)} entry={entry} />
        ))}
      </tbody>
    </table>
  );
}

function TransactionRow({ entry }: { entry: LedgerEntry }) {
  return (
    <tr>
      <td>{entry.date}</td>
      <th scope="row">{transactionTypeLabel(entry.kind)}</th>
      <td className="num">{formatDecimal(entry.units)}</td>
      <td className="num">{formatDecimal(entry.amount)}</td>
      <td>{entry.notes ?? ""}</td>
    </tr>
  );
}

function rowKey(entry: LedgerEntry): string {
  return `${entry.date}-${entry.kind}-${entry.description}`;
}
