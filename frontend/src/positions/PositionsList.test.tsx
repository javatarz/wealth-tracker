import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { respond, stubRoutes } from "../test/fetchRoutes";
import { PositionsList } from "./PositionsList";

const positions = [
  {
    id: "7f1d6f8e-35a4-4c55-9df2-6f0f6b0c1a11",
    scheme: "HDFC Top 200 Fund - Direct Plan - Growth",
    institution: "HDFC Mutual Fund",
    folio: "1234567890",
    units: "1830.270",
    cost_basis: "129871.58",
  },
  {
    id: "0b3c4f9a-8d2e-4c71-a5b6-1e2f3a4b5c6d",
    scheme: "SBI Equity Hybrid Fund - Direct Plan - Growth",
    institution: "SBI Mutual Fund",
    folio: "9876543210",
    units: "564.781",
    cost_basis: "45135.00",
  },
];

describe("PositionsList", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("lists each Position with its Account, units and cost basis", async () => {
    stubRoutes({ "GET /api/positions": () => respond(200, positions) });

    render(<PositionsList onImport={vi.fn()} />);

    const sbi = await screen.findByRole("row", { name: /SBI Equity Hybrid/ });
    expect(
      within(sbi)
        .getAllByRole("cell")
        .map((c) => c.textContent),
    ).toEqual(["SBI Mutual Fund · 9876543210", "564.781", "45,135.00"]);
    expect(screen.getAllByRole("row")).toHaveLength(3);
  });

  it("offers an import when there are no Positions yet", async () => {
    stubRoutes({ "GET /api/positions": () => respond(200, []) });
    const onImport = vi.fn();

    render(<PositionsList onImport={onImport} />);
    await userEvent.click(
      await screen.findByRole("button", { name: "Import a statement" }),
    );

    expect(onImport).toHaveBeenCalledOnce();
  });

  it("says so when the server can't be reached", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.reject(new TypeError("Failed to fetch"))),
    );

    render(<PositionsList onImport={vi.fn()} />);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Couldn't reach the Wealth Tracker server.",
    );
  });
});
