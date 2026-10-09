import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";
import { respond, stubRoutes } from "./test/fetchRoutes";

const position = {
  id: "7f1d6f8e-35a4-4c55-9df2-6f0f6b0c1a11",
  scheme: "HDFC Top 200 Fund - Direct Plan - Growth",
  institution: "HDFC Mutual Fund",
  folio: "1234567890",
  units: "1830.270",
  cost_basis: "129871.58",
};

const preview = {
  parser: { name: "casparser", version: "1.4.1" },
  file_type: "CAMS",
  cas_type: "DETAILED",
  statement_period: { from: "01-Apr-2024", to: "31-Mar-2025" },
  parse_warnings: [],
  folios: [],
};

function pdf() {
  return new File(["%PDF-1.4"], "cas.pdf", { type: "application/pdf" });
}

describe("App", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows the API health status", async () => {
    stubRoutes({
      "GET /api/health": () => respond(200, { status: "ok" }),
      "GET /api/positions": () => respond(200, []),
    });

    render(<App />);

    expect(await screen.findByText("ok")).toBeInTheDocument();
  });

  it("shows an error when the API is unreachable", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.reject(new TypeError("Failed to fetch"))),
    );

    render(<App />);

    expect(await screen.findByText(/Failed to fetch/)).toBeInTheDocument();
  });

  it("opens the Goals tab from the Sections nav", async () => {
    stubRoutes({
      "GET /api/health": () => respond(200, { status: "ok" }),
      "GET /api/positions": () => respond(200, []),
      "GET /api/goals": () => respond(200, []),
      "GET /api/accounts": () => respond(200, []),
    });
    render(<App />);

    await userEvent.click(await screen.findByRole("button", { name: "Goals" }));

    expect(await screen.findByText(/No Goals yet/)).toBeInTheDocument();
  });

  it("commits a previewed statement and lands on its Positions", async () => {
    let committed = false;
    stubRoutes({
      "GET /api/health": () => respond(200, { status: "ok" }),
      "GET /api/positions": () => respond(200, committed ? [position] : []),
      "POST /api/statements/preview": () => respond(200, preview),
      "POST /api/imports": () => {
        committed = true;
        return respond(201, {
          import_id: position.id,
          positions: 1,
          transactions: 7,
        });
      },
    });
    render(<App />);

    await userEvent.click(
      await screen.findByRole("button", { name: "Import a statement" }),
    );
    await userEvent.upload(screen.getByLabelText("Choose file"), pdf());
    await userEvent.click(
      await screen.findByRole("button", { name: "Commit import" }),
    );

    const row = await screen.findByRole("row", { name: /HDFC Top 200 Fund/ });
    expect(row).toHaveTextContent("1,830.270");
    expect(row).toHaveTextContent("1,29,871.58");
    expect(screen.getByRole("button", { name: "Positions" })).toHaveAttribute(
      "aria-current",
      "page",
    );
  });
});
