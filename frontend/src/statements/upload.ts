export interface Upload {
  file: File;
  password: string;
}

/** Request options that send an Upload as the multipart form the API expects. */
export function asForm(
  { file, password }: Upload,
  extra: Record<string, string> = {},
) {
  return {
    // openapi-typescript types binary uploads as string.
    body: { file: file as unknown as string, password, ...extra },
    bodySerializer: () => {
      const form = new FormData();
      form.append("file", file);
      form.append("password", password);
      Object.entries(extra).forEach(([name, value]) => {
        form.append(name, value);
      });
      return form;
    },
  };
}
