export interface Upload {
  file: File;
  password: string;
}

/** Request options that send an Upload as the multipart form the API expects. */
export function asForm({ file, password }: Upload) {
  return {
    // openapi-typescript types binary uploads as string.
    body: { file: file as unknown as string, password },
    bodySerializer: () => {
      const form = new FormData();
      form.append("file", file);
      form.append("password", password);
      return form;
    },
  };
}
