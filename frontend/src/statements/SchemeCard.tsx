import { formatDecimal } from "./formatDecimal";
import type { StatementPreview } from "./previewStatement";

type Scheme = StatementPreview["folios"][number]["schemes"][number];
type Transaction = Scheme["transactions"][number];

interface Fact {
  term: string;
  detail: string;
  className?: string;
}

const COLUMNS = [
  { label: "Date" },
  { label: "Description" },
  { label: "Type" },
  { label: "Amount (₹)", className: "num" },
  { label: "Units", className: "num" },
  { label: "NAV", className: "num" },
  { label: "Balance", className: "num" },
];

const DECIMAL_FIELDS = ["amount", "units", "nav", "balance"] as const;

export function SchemeCard({ scheme }: { scheme: Scheme }) {
  return (
    <article className="scheme" aria-label={scheme.scheme}>
      <h4>{scheme.scheme}</h4>
      <SchemeFacts facts={factsOf(scheme)} />
      <TransactionTable transactions={scheme.transactions} />
    </article>
  );
}

function factsOf(scheme: Scheme): Fact[] {
  const { valuation } = scheme;
  return [
    { term: "ISIN", detail: scheme.isin ?? "Not found", className: "mono" },
    { term: "AMFI", detail: scheme.amfi ?? "—", className: "mono" },
    { term: "Registrar", detail: scheme.rta },
    {
      term: "Opening units",
      detail: formatDecimal(scheme.open),
      className: "num",
    },
    {
      term: "Closing units",
      detail: formatDecimal(scheme.close),
      className: "num",
    },
    {
      term: `Value on ${valuation.date}`,
      detail: `₹${formatDecimal(valuation.value)} @ ${formatDecimal(valuation.nav)}`,
      className: "num",
    },
  ];
}

function SchemeFacts({ facts }: { facts: Fact[] }) {
  return (
    <dl className="scheme-meta">
      {facts.map((fact) => (
        <div key={fact.term}>
          <dt>{fact.term}</dt>
          <dd className={fact.className}>{fact.detail}</dd>
        </div>
      ))}
    </dl>
  );
}

function TransactionTable({ transactions }: { transactions: Transaction[] }) {
  return (
    <table>
      <thead>
        <tr>
          {COLUMNS.map((column) => (
            <th key={column.label} scope="col" className={column.className}>
              {column.label}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {transactions.map((transaction, index) => (
          <TransactionRow key={index} transaction={transaction} />
        ))}
      </tbody>
    </table>
  );
}

function TransactionRow({ transaction }: { transaction: Transaction }) {
  return (
    <tr>
      <td className="nowrap">{transaction.date}</td>
      <td>{transaction.description}</td>
      <td className="mono small">{transaction.type}</td>
      {DECIMAL_FIELDS.map((field) => (
        <td key={field} className="num">
          {formatDecimal(transaction[field])}
        </td>
      ))}
    </tr>
  );
}
