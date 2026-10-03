import { formatDecimal } from "./formatDecimal";
import type { StatementPreview as Preview } from "./previewStatement";

type Scheme = Preview["folios"][number]["schemes"][number];

export function StatementPreview({
  preview,
  fileName,
}: {
  preview: Preview;
  fileName: string;
}) {
  const schemeCount = preview.folios.reduce(
    (total, folio) => total + folio.schemes.length,
    0,
  );

  return (
    <section aria-labelledby="preview-heading" className="preview">
      <header className="preview-header">
        <h2 id="preview-heading">{fileName}</h2>
        <p className="muted">
          {preview.file_type} {preview.cas_type.toLowerCase()} statement,{" "}
          {preview.statement_period.from} to {preview.statement_period.to} ·{" "}
          {preview.folios.length} folios · {schemeCount} schemes
        </p>
        <p className="muted small">
          Parsed with {preview.parser.name} {preview.parser.version}. Preview
          only — nothing has been saved.
        </p>
      </header>

      {preview.parse_warnings.length > 0 && (
        <section aria-labelledby="warnings-heading" className="callout warn">
          <h3 id="warnings-heading">
            Parse warnings ({preview.parse_warnings.length})
          </h3>
          <p className="small">
            The parser found rows that don't reconcile with the statement's own
            running balance. Check these schemes against the PDF.
          </p>
          <ul>
            {preview.parse_warnings.map((warning, index) => (
              <li key={index}>{warning}</li>
            ))}
          </ul>
        </section>
      )}

      {preview.folios.map((folio, folioIndex) => (
        <section
          key={`${folio.folio}-${folio.amc}-${String(folioIndex)}`}
          aria-label={`Folio ${folio.folio}, ${folio.amc}`}
          className="folio"
        >
          <h3>
            Folio <span className="mono">{folio.folio}</span> · {folio.amc}
          </h3>
          {folio.schemes.map((scheme, schemeIndex) => (
            <SchemeCard
              key={`${scheme.rta_code}-${String(schemeIndex)}`}
              scheme={scheme}
            />
          ))}
        </section>
      ))}
    </section>
  );
}

function SchemeCard({ scheme }: { scheme: Scheme }) {
  return (
    <article className="scheme" aria-label={scheme.scheme}>
      <h4>{scheme.scheme}</h4>
      <dl className="scheme-meta">
        <div>
          <dt>ISIN</dt>
          <dd className="mono">{scheme.isin ?? "Not found"}</dd>
        </div>
        <div>
          <dt>AMFI</dt>
          <dd className="mono">{scheme.amfi ?? "—"}</dd>
        </div>
        <div>
          <dt>Registrar</dt>
          <dd>{scheme.rta}</dd>
        </div>
        <div>
          <dt>Opening units</dt>
          <dd className="num">{formatDecimal(scheme.open)}</dd>
        </div>
        <div>
          <dt>Closing units</dt>
          <dd className="num">{formatDecimal(scheme.close)}</dd>
        </div>
        <div>
          <dt>Value on {scheme.valuation.date}</dt>
          <dd className="num">
            ₹{formatDecimal(scheme.valuation.value)} @{" "}
            {formatDecimal(scheme.valuation.nav)}
          </dd>
        </div>
      </dl>
      <table>
        <thead>
          <tr>
            <th scope="col">Date</th>
            <th scope="col">Description</th>
            <th scope="col">Type</th>
            <th scope="col" className="num">
              Amount (₹)
            </th>
            <th scope="col" className="num">
              Units
            </th>
            <th scope="col" className="num">
              NAV
            </th>
            <th scope="col" className="num">
              Balance
            </th>
          </tr>
        </thead>
        <tbody>
          {scheme.transactions.map((txn, index) => (
            <tr key={index}>
              <td className="nowrap">{txn.date}</td>
              <td>{txn.description}</td>
              <td className="mono small">{txn.type}</td>
              <td className="num">{formatDecimal(txn.amount)}</td>
              <td className="num">{formatDecimal(txn.units)}</td>
              <td className="num">{formatDecimal(txn.nav)}</td>
              <td className="num">{formatDecimal(txn.balance)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </article>
  );
}
