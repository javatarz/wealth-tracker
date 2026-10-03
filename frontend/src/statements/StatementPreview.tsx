import type { StatementPreview as Preview } from "./previewStatement";
import { SchemeCard } from "./SchemeCard";

type Folio = Preview["folios"][number];

interface PreviewProps {
  preview: Preview;
  fileName: string;
}

export function StatementPreview({ preview, fileName }: PreviewProps) {
  return (
    <section aria-labelledby="preview-heading" className="preview">
      <PreviewHeader preview={preview} fileName={fileName} />
      <ParseWarnings warnings={preview.parse_warnings} />
      {preview.folios.map((folio, index) => (
        <FolioSection
          key={`${folio.folio}-${folio.amc}-${String(index)}`}
          folio={folio}
        />
      ))}
    </section>
  );
}

function PreviewHeader({ preview, fileName }: PreviewProps) {
  const schemeCount = preview.folios.reduce(
    (total, folio) => total + folio.schemes.length,
    0,
  );

  return (
    <header className="preview-header">
      <h2 id="preview-heading">{fileName}</h2>
      <p className="muted">
        {preview.file_type} {preview.cas_type.toLowerCase()} statement,{" "}
        {preview.statement_period.from} to {preview.statement_period.to} ·{" "}
        {preview.folios.length} folios · {schemeCount} schemes
      </p>
      <p className="muted small">
        Parsed with {preview.parser.name} {preview.parser.version}. Preview only
        — nothing has been saved.
      </p>
    </header>
  );
}

function ParseWarnings({ warnings }: { warnings: string[] }) {
  if (warnings.length === 0) {
    return null;
  }

  return (
    <section aria-labelledby="warnings-heading" className="callout warn">
      <h3 id="warnings-heading">Parse warnings ({warnings.length})</h3>
      <p className="small">
        The parser found rows that don't reconcile with the statement's own
        running balance. Check these schemes against the PDF.
      </p>
      <ul>
        {warnings.map((warning, index) => (
          <li key={index}>{warning}</li>
        ))}
      </ul>
    </section>
  );
}

function FolioSection({ folio }: { folio: Folio }) {
  return (
    <section
      aria-label={`Folio ${folio.folio}, ${folio.amc}`}
      className="folio"
    >
      <h3>
        Folio <span className="mono">{folio.folio}</span> · {folio.amc}
      </h3>
      {folio.schemes.map((scheme, index) => (
        <SchemeCard
          key={`${scheme.rta_code}-${String(index)}`}
          scheme={scheme}
        />
      ))}
    </section>
  );
}
