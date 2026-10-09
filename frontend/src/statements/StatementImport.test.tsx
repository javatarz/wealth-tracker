import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi, type Mock } from "vitest";

import type { components } from "../api/schema";
import { StatementImport } from "./StatementImport";

type Preview = components["schemas"]["StatementPreview"];

const preview: Preview = {
  parser: { name: "casparser", version: "1.4.1" },
  file_type: "CAMS",
  cas_type: "DETAILED",
  statement_period: { from: "01-Apr-2024", to: "31-Mar-2025" },
  parse_warnings: [],
  folios: [
    {
      folio: "1234567890",
      amc: "HDFC Mutual Fund",
      schemes: [
        {
          scheme: "HDFC Top 200 Fund - Direct Plan - Growth",
          isin: "INF179KA1RQ7",
          amfi: "130498",
          type: "EQUITY",
          rta: "CAMS",
          rta_code: "HGFG",
          advisor: null,
          open: "0",
          close: "1594.821",
          close_calculated: "1594.821",
          valuation: {
            date: "2025-03-31",
            nav: "70.7416",
            cost: null,
            value: "112819.06",
          },
          transactions: [
            {
              date: "2024-04-02",
              description: "Purchase",
              type: "PURCHASE",
              amount: "-76739.54",
              units: "1136.067",
              nav: "67.5484",
              balance: "1136.067",
              dividend_rate: null,
            },
            {
              date: "2024-05-17",
              description: "Purchase",
              type: "PURCHASE",
              amount: "-35451.48",
              units: "458.754",
              nav: "77.2778",
              balance: "1594.821",
              dividend_rate: null,
            },
          ],
        },
      ],
    },
  ],
};

function respond(status: number, body: unknown) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function pdf(name = "cas.pdf") {
  return new File(["%PDF-1.4"], name, { type: "application/pdf" });
}

async function passwordSent(fetchMock: Mock<typeof fetch>, call: number) {
  const request = fetchMock.mock.calls[call]?.[0] as Request;
  const form = await request.formData();
  return form.get("password");
}

describe("StatementImport", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("uploads a chosen file and shows folios, schemes and transactions", async () => {
    const fetchMock = vi.fn<typeof fetch>(() =>
      Promise.resolve(respond(200, preview)),
    );
    vi.stubGlobal("fetch", fetchMock);
    render(<StatementImport onCommitted={vi.fn()} />);

    await userEvent.upload(screen.getByLabelText("Choose file"), pdf());

    const folio = await screen.findByRole("region", {
      name: "Folio 1234567890, HDFC Mutual Fund",
    });
    const scheme = within(folio).getByRole("article", {
      name: "HDFC Top 200 Fund - Direct Plan - Growth",
    });
    const rows = within(scheme).getAllByRole("row");
    expect(rows).toHaveLength(3);
    expect(rows[2]).toHaveTextContent("2024-05-17");
    expect(rows[2]).toHaveTextContent("−35,451.48");
    expect(rows[2]).toHaveTextContent("1,594.821");
    expect(
      screen.getByText(/Parsed with casparser 1\.4\.1/),
    ).toBeInTheDocument();
    expect(screen.queryByText(/Parse warnings/)).not.toBeInTheDocument();

    const request = fetchMock.mock.calls[0]?.[0] as Request;
    expect(request.url).toMatch(/\/api\/statements\/preview$/);
    expect(request.method).toBe("POST");
  });

  it("accepts a dropped file and shows progress while parsing", async () => {
    let resolve: (response: Response) => void = () => undefined;
    vi.stubGlobal(
      "fetch",
      vi.fn(
        () =>
          new Promise<Response>((r) => {
            resolve = r;
          }),
      ),
    );
    render(<StatementImport onCommitted={vi.fn()} />);

    fireEvent.drop(screen.getByTestId("dropzone"), {
      dataTransfer: { files: [pdf("dropped.pdf")] },
    });

    expect(
      await screen.findByRole("progressbar", { name: "Parsing statement" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Parsing dropped.pdf…")).toBeInTheDocument();
    expect(screen.getByLabelText("Choose file")).toBeDisabled();

    resolve(respond(200, preview));

    expect(
      await screen.findByRole("heading", { name: "dropped.pdf" }),
    ).toBeInTheDocument();
    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
  });

  it("surfaces parse warnings", async () => {
    const warning = "Balance mismatch in HDFC Top 200 Fund on 2024-05-17";
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve(
          respond(200, { ...preview, parse_warnings: [warning] }),
        ),
      ),
    );
    render(<StatementImport onCommitted={vi.fn()} />);

    await userEvent.upload(screen.getByLabelText("Choose file"), pdf());

    const warnings = await screen.findByRole("region", {
      name: "Parse warnings (1)",
    });
    expect(warnings).toHaveTextContent(warning);
  });

  it("shows a clear error for an invalid PDF", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve(
          respond(400, {
            code: "unrecognised_statement",
            message: "This file isn't an original CAMS or KFintech statement.",
          }),
        ),
      ),
    );
    render(<StatementImport onCommitted={vi.fn()} />);

    await userEvent.upload(screen.getByLabelText("Choose file"), pdf());

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "This file isn't an original CAMS or KFintech statement.",
    );
    expect(screen.getByLabelText("Choose file")).toBeEnabled();
  });

  it("shows an error when the server is unreachable", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.reject(new TypeError("Failed to fetch"))),
    );
    render(<StatementImport onCommitted={vi.fn()} />);

    await userEvent.upload(screen.getByLabelText("Choose file"), pdf());

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Couldn't reach the Wealth Tracker server.",
    );
  });

  it("asks for the password and retries without re-uploading", async () => {
    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(
        respond(400, {
          code: "password_required",
          message: "This statement is password-protected.",
        }),
      )
      .mockResolvedValueOnce(respond(200, preview));
    vi.stubGlobal("fetch", fetchMock);
    render(<StatementImport onCommitted={vi.fn()} />);

    await userEvent.upload(
      screen.getByLabelText("Choose file"),
      pdf("locked.pdf"),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "This statement is password-protected.",
    );

    await userEvent.type(
      screen.getByLabelText("Statement password"),
      "ABCDE1234F",
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Open statement" }),
    );

    expect(
      await screen.findByRole("heading", { name: "locked.pdf" }),
    ).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(await passwordSent(fetchMock, 0)).toBe("");
    expect(await passwordSent(fetchMock, 1)).toBe("ABCDE1234F");
  });

  it("highlights an incorrect password and lets the user retry", async () => {
    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(
        respond(400, {
          code: "password_required",
          message: "This statement is password-protected.",
        }),
      )
      .mockResolvedValueOnce(
        respond(400, {
          code: "incorrect_password",
          message: "That password didn't open the statement.",
        }),
      );
    vi.stubGlobal("fetch", fetchMock);
    render(<StatementImport onCommitted={vi.fn()} />);

    await userEvent.upload(screen.getByLabelText("Choose file"), pdf());
    expect(await screen.findByRole("alert")).not.toHaveClass("bad-text");

    await userEvent.type(screen.getByLabelText("Statement password"), "nope");
    await userEvent.click(
      screen.getByRole("button", { name: "Open statement" }),
    );

    const alert = await screen.findByText(/didn't open the statement/);
    expect(alert).toHaveClass("bad-text");
    expect(screen.getByLabelText("Statement password")).toHaveValue("");
  });

  it("commits the previewed statement with the password that opened it", async () => {
    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(respond(200, preview))
      .mockResolvedValueOnce(
        respond(201, { import_id: "x", positions: 1, transactions: 2 }),
      );
    vi.stubGlobal("fetch", fetchMock);
    const onCommitted = vi.fn();
    render(<StatementImport onCommitted={onCommitted} />);

    await userEvent.upload(screen.getByLabelText("Choose file"), pdf());
    await userEvent.click(
      await screen.findByRole("button", { name: "Commit import" }),
    );

    await vi.waitFor(() => {
      expect(onCommitted).toHaveBeenCalledOnce();
    });
    const request = fetchMock.mock.calls[1]?.[0] as Request;
    expect(request.url).toMatch(/\/api\/imports$/);
    expect(await passwordSent(fetchMock, 1)).toBe("");
  });

  it("keeps the preview and explains why a commit was refused", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn<typeof fetch>()
        .mockResolvedValueOnce(respond(200, preview))
        .mockResolvedValueOnce(
          respond(409, {
            code: "already_imported",
            message: "This statement has already been imported.",
          }),
        ),
    );
    const onCommitted = vi.fn();
    render(<StatementImport onCommitted={onCommitted} />);

    await userEvent.upload(screen.getByLabelText("Choose file"), pdf());
    await userEvent.click(
      await screen.findByRole("button", { name: "Commit import" }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "This statement has already been imported.",
    );
    expect(screen.getByRole("button", { name: "Commit import" })).toBeEnabled();
    expect(
      screen.getByRole("heading", { name: "cas.pdf" }),
    ).toBeInTheDocument();
    expect(onCommitted).not.toHaveBeenCalled();
  });
});
