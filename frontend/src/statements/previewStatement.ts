import { api } from "../api/client";
import type { components } from "../api/schema";

export type StatementPreview = components["schemas"]["StatementPreview"];
export type StatementErrorCode =
  components["schemas"]["StatementError"]["code"];

export type PreviewResult =
  | { kind: "ok"; preview: StatementPreview }
  | { kind: "error"; code: StatementErrorCode | "network"; message: string };

type UploadResponse = Awaited<ReturnType<typeof upload>>;

const REJECTED: PreviewResult = {
  kind: "error",
  code: "parse_failed",
  message: "The upload was rejected by the server.",
};

const UNREACHABLE: PreviewResult = {
  kind: "error",
  code: "network",
  message: "Couldn't reach the Wealth Tracker server.",
};

export async function previewStatement(
  file: File,
  password: string,
): Promise<PreviewResult> {
  try {
    return toResult(await upload(file, password));
  } catch {
    return UNREACHABLE;
  }
}

function upload(file: File, password: string) {
  return api.POST("/api/statements/preview", {
    // openapi-typescript types binary uploads as string.
    body: { file: file as unknown as string, password },
    bodySerializer: (body) => {
      const form = new FormData();
      form.append("file", file);
      form.append("password", body.password);
      return form;
    },
  });
}

function toResult(response: UploadResponse): PreviewResult {
  const { data, error } = response;
  return data ? { kind: "ok", preview: data } : toFailure(error);
}

function toFailure(error: NonNullable<UploadResponse["error"]>): PreviewResult {
  return "code" in error
    ? { kind: "error", code: error.code, message: error.message }
    : REJECTED;
}
