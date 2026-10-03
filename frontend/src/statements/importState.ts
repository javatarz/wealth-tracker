import type { PreviewResult, StatementPreview } from "./previewStatement";
import type { Upload } from "./upload";

export type ImportState =
  | { kind: "idle" }
  | { kind: "parsing"; upload: Upload }
  | { kind: "needsPassword"; upload: Upload; message: string }
  | { kind: "wrongPassword"; upload: Upload; message: string }
  | { kind: "error"; message: string }
  | { kind: "preview"; upload: Upload; preview: StatementPreview };

type ResultKind = PreviewResult["kind"];
type ResultOf<K extends ResultKind> = Extract<PreviewResult, { kind: K }>;
type Failure = ResultOf<"error">;
type Transition<K extends ResultKind> = (
  upload: Upload,
  result: ResultOf<K>,
) => ImportState;

const showError: Transition<"error"> = (_upload, { message }) => ({
  kind: "error",
  message,
});

const failureTransitions: Partial<
  Record<Failure["code"], Transition<"error">>
> = {
  password_required: (upload, { message }) => ({
    kind: "needsPassword",
    upload,
    message,
  }),
  incorrect_password: (upload, { message }) => ({
    kind: "wrongPassword",
    upload,
    message,
  }),
};

const transitions: { [K in ResultKind]: Transition<K> } = {
  ok: (upload, { preview }) => ({ kind: "preview", upload, preview }),
  error: (upload, failure) =>
    (failureTransitions[failure.code] ?? showError)(upload, failure),
};

function transition<K extends ResultKind>(
  kind: K,
  upload: Upload,
  result: ResultOf<K>,
): ImportState {
  return transitions[kind](upload, result);
}

export function stateAfter(upload: Upload, result: PreviewResult): ImportState {
  return transition(result.kind, upload, result);
}
