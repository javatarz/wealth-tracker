import type { ReactNode } from "react";

import { CommitImport } from "./CommitImport";
import type { ImportState } from "./importState";
import { PasswordPrompt } from "./PasswordPrompt";
import { StatementPreview } from "./StatementPreview";
import type { Upload } from "./upload";

type Kind = ImportState["kind"];
type StateOf<K extends Kind> = Extract<ImportState, { kind: K }>;

export interface ImportActions {
  retry: (upload: Upload) => void;
  committed: () => void;
}

type Outcome<K extends Kind> = (
  state: StateOf<K>,
  actions: ImportActions,
) => ReactNode;

function passwordPrompt(tone: "neutral" | "bad"): Outcome<"needsPassword"> {
  return ({ upload, message }, { retry }) => (
    <PasswordPrompt
      fileName={upload.file.name}
      message={message}
      tone={tone}
      onSubmit={(password) => {
        retry({ file: upload.file, password });
      }}
    />
  );
}

const outcomes: { [K in Kind]: Outcome<K> } = {
  idle: () => null,
  parsing: ({ upload }) => (
    <div role="status" className="parsing">
      <progress aria-label="Parsing statement" />
      <span>Parsing {upload.file.name}…</span>
    </div>
  ),
  needsPassword: passwordPrompt("neutral"),
  wrongPassword: (state, actions) =>
    passwordPrompt("bad")({ ...state, kind: "needsPassword" }, actions),
  error: ({ message }) => (
    <p role="alert" className="callout bad">
      {message}
    </p>
  ),
  preview: ({ upload, preview }, { committed }) => (
    <>
      <CommitImport upload={upload} onCommitted={committed} />
      <StatementPreview preview={preview} fileName={upload.file.name} />
    </>
  ),
};

function renderOutcome<K extends Kind>(
  kind: K,
  state: StateOf<K>,
  actions: ImportActions,
): ReactNode {
  return outcomes[kind](state, actions);
}

export function ImportOutcome({
  state,
  actions,
}: {
  state: ImportState;
  actions: ImportActions;
}) {
  return renderOutcome(state.kind, state, actions);
}
