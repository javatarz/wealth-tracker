import type { ReactNode } from "react";

import type { ImportState } from "./importState";
import { PasswordPrompt } from "./PasswordPrompt";
import { StatementPreview } from "./StatementPreview";

type Kind = ImportState["kind"];
type StateOf<K extends Kind> = Extract<ImportState, { kind: K }>;
type Retry = (file: File, password: string) => void;
type Outcome<K extends Kind> = (state: StateOf<K>, retry: Retry) => ReactNode;

const outcomes: { [K in Kind]: Outcome<K> } = {
  idle: () => null,
  parsing: ({ file }) => (
    <div role="status" className="parsing">
      <progress aria-label="Parsing statement" />
      <span>Parsing {file.name}…</span>
    </div>
  ),
  needsPassword: ({ file, message }, retry) => (
    <PasswordPrompt
      fileName={file.name}
      message={message}
      tone="neutral"
      onSubmit={(password) => {
        retry(file, password);
      }}
    />
  ),
  wrongPassword: ({ file, message }, retry) => (
    <PasswordPrompt
      fileName={file.name}
      message={message}
      tone="bad"
      onSubmit={(password) => {
        retry(file, password);
      }}
    />
  ),
  error: ({ message }) => (
    <p role="alert" className="callout bad">
      {message}
    </p>
  ),
  preview: ({ file, preview }) => (
    <StatementPreview preview={preview} fileName={file.name} />
  ),
};

function renderOutcome<K extends Kind>(
  kind: K,
  state: StateOf<K>,
  retry: Retry,
): ReactNode {
  return outcomes[kind](state, retry);
}

export function ImportOutcome({
  state,
  retry,
}: {
  state: ImportState;
  retry: Retry;
}) {
  return renderOutcome(state.kind, state, retry);
}
