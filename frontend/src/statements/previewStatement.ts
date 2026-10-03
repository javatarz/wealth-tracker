import { api } from "../api/client";
import type { components } from "../api/schema";

export type StatementPreview = components["schemas"]["StatementPreview"];
export type StatementErrorCode =
  components["schemas"]["StatementError"]["code"];

export type PreviewResult =
  | { kind: "ok"; preview: StatementPreview }
  | { kind: "error"; code: StatementErrorCode | "network"; message: string };

export async function previewStatement(
  file: File,
  password: string,
): Promise<PreviewResult> {
  try {
    const { data, error } = await api.POST("/api/statements/preview", {
      // openapi-typescript types binary uploads as string.
      body: { file: file as unknown as string, password },
      bodySerializer: (body) => {
        const form = new FormData();
        form.append("file", file);
        form.append("password", body.password);
        return form;
      },
    });
    if (data) {
      return { kind: "ok", preview: data };
    }
    if ("code" in error) {
      return { kind: "error", code: error.code, message: error.message };
    }
    return {
      kind: "error",
      code: "parse_failed",
      message: "The upload was rejected by the server.",
    };
  } catch {
    return {
      kind: "error",
      code: "network",
      message: "Couldn't reach the Wealth Tracker server.",
    };
  }
}
