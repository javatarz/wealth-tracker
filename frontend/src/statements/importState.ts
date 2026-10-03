import type { PreviewResult, StatementPreview } from "./previewStatement";

export type ImportState =
  | { kind: "idle" }
  | { kind: "parsing"; file: File }
  | { kind: "needsPassword"; file: File; message: string }
  | { kind: "wrongPassword"; file: File; message: string }
  | { kind: "error"; message: string }
  | { kind: "preview"; file: File; preview: StatementPreview };

type ResultKind = PreviewResult["kind"];
type ResultOf<K extends ResultKind> = Extract<PreviewResult, { kind: K }>;
type Failure = ResultOf<"error">;
type Transition<K extends ResultKind> = (
  file: File,
  result: ResultOf<K>,
) => ImportState;

const showError: Transition<"error"> = (_file, { message }) => ({
  kind: "error",
  message,
});

const failureTransitions: Partial<
  Record<Failure["code"], Transition<"error">>
> = {
  password_required: (file, { message }) => ({
    kind: "needsPassword",
    file,
    message,
  }),
  incorrect_password: (file, { message }) => ({
    kind: "wrongPassword",
    file,
    message,
  }),
};

const transitions: { [K in ResultKind]: Transition<K> } = {
  ok: (file, { preview }) => ({ kind: "preview", file, preview }),
  error: (file, failure) =>
    (failureTransitions[failure.code] ?? showError)(file, failure),
};

function transition<K extends ResultKind>(
  kind: K,
  file: File,
  result: ResultOf<K>,
): ImportState {
  return transitions[kind](file, result);
}

export function stateAfter(file: File, result: PreviewResult): ImportState {
  return transition(result.kind, file, result);
}
