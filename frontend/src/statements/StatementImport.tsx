import { useState, type DragEvent, type SubmitEvent } from "react";

import { previewStatement, type StatementPreview } from "./previewStatement";
import { StatementPreview as PreviewView } from "./StatementPreview";

type State =
  | { kind: "idle" }
  | { kind: "parsing"; file: File }
  | { kind: "needsPassword"; file: File; message: string }
  | { kind: "error"; message: string }
  | { kind: "preview"; file: File; preview: StatementPreview };

export function StatementImport() {
  const [state, setState] = useState<State>({ kind: "idle" });
  const [dragging, setDragging] = useState(false);
  const [password, setPassword] = useState("");
  const parsing = state.kind === "parsing";

  async function parse(file: File, withPassword: string) {
    setState({ kind: "parsing", file });
    const result = await previewStatement(file, withPassword);
    setPassword("");
    if (result.kind === "ok") {
      setState({ kind: "preview", file, preview: result.preview });
    } else if (
      result.code === "password_required" ||
      result.code === "incorrect_password"
    ) {
      setState({ kind: "needsPassword", file, message: result.message });
    } else {
      setState({ kind: "error", message: result.message });
    }
  }

  function choose(files: FileList | null) {
    const file = files?.[0];
    if (file && !parsing) {
      void parse(file, "");
    }
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);
    choose(event.dataTransfer.files);
  }

  function onPasswordSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (state.kind === "needsPassword") {
      void parse(state.file, password);
    }
  }

  return (
    <section aria-labelledby="import-heading">
      <h2 id="import-heading">Preview a CAMS statement</h2>
      <div
        className={`dropzone${dragging ? " dragging" : ""}`}
        data-testid="dropzone"
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(!parsing);
        }}
        onDragLeave={() => {
          setDragging(false);
        }}
        onDrop={onDrop}
      >
        <p>Drop a CAMS or KFintech Consolidated Account Statement PDF here</p>
        <label className={`btn${parsing ? " disabled" : ""}`}>
          Choose file
          <input
            type="file"
            accept="application/pdf,.pdf"
            className="visually-hidden"
            disabled={parsing}
            onChange={(event) => {
              choose(event.target.files);
              event.target.value = "";
            }}
          />
        </label>
        <p className="muted small">
          The file is read on this machine and discarded. Nothing is stored.
        </p>
      </div>

      {state.kind === "parsing" && (
        <div role="status" className="parsing">
          <progress aria-label="Parsing statement" />
          <span>Parsing {state.file.name}…</span>
        </div>
      )}

      {state.kind === "needsPassword" && (
        <form className="callout" onSubmit={onPasswordSubmit}>
          <p role="alert">
            {state.message} Enter its password to open {state.file.name}.
          </p>
          <label>
            Statement password
            <input
              type="password"
              autoComplete="off"
              value={password}
              onChange={(event) => {
                setPassword(event.target.value);
              }}
            />
          </label>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={!password}
          >
            Open statement
          </button>
        </form>
      )}

      {state.kind === "error" && (
        <p role="alert" className="callout bad">
          {state.message}
        </p>
      )}

      {state.kind === "preview" && (
        <PreviewView preview={state.preview} fileName={state.file.name} />
      )}
    </section>
  );
}
