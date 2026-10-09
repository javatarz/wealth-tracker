import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { respond, stubRoutes } from "../test/fetchRoutes";
import { PositionDetail } from "./PositionDetail";

const ID = "7f1d6f8e-35a4-4c55-9df2-6f0f6b0c1a11";

function position(overrides: Record<string, unknown> = {}) {
  return {
    id: ID,
    scheme: "SBI Equity Hybrid Fund - Direct Plan - Growth",
    institution: "SBI Mutual Fund",
    folio: "9876543210",
    units: "564.781",
    cost_basis: "45135.00",
    value: "60000.00",
    valuation_strategy: "market_priced",
    valuation_label: "Market-priced",
    stale: false,
    warning: null,
    ...overrides,
  };
}

const history = [
  {
    date: "2025-03-31",
    value: "60000.00",
    strategy: "market_priced",
    priced_on: "2025-03-31",
    stale: false,
    warning: null,
  },
];

function routes(overrides: Record<string, unknown> = {}, points = history) {
  return {
    [`GET /api/positions/${ID}`]: () => respond(200, position(overrides)),
    [`GET /api/positions/${ID}/valuation-history`]: () => respond(200, points),
  };
}

describe("PositionDetail", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows the computed value, strategy and valuation history", async () => {
    stubRoutes(routes());

    render(<PositionDetail id={ID} onBack={vi.fn()} />);

    expect(await screen.findAllByText("60,000.00")).toHaveLength(2); // the current value and its history point
    expect(screen.getByText("Market-priced")).toBeInTheDocument();
    const row = screen.getByRole("row", { name: /2025-03-31/ });
    expect(within(row).getAllByRole("cell")[0]).toHaveTextContent("60,000.00");
  });

  it("warns when market data is stale", async () => {
    stubRoutes(
      routes({ stale: true, warning: "No cached NAV for this Instrument." }),
    );

    render(<PositionDetail id={ID} onBack={vi.fn()} />);

    expect(
      await screen.findByText("No cached NAV for this Instrument."),
    ).toBeInTheDocument();
    expect(screen.getByText("Market data is stale.")).toBeInTheDocument();
  });

  it("lets the user record an appraised value for an appraised Instrument", async () => {
    let recorded: unknown;
    const fetchMock = stubRoutes({
      ...routes({
        valuation_strategy: "appraised",
        valuation_label: "Appraised",
        value: null,
      }),
      [`POST /api/positions/${ID}/appraisal`]: (request) => {
        recorded = request;
        return respond(201, {
          instrument_id: "0b3c4f9a-8d2e-4c71-a5b6-1e2f3a4b5c6d",
          date: "2025-03-31",
          value: "750000.00",
          recorded_at: "2025-03-31T00:00:00Z",
        });
      },
    });

    render(<PositionDetail id={ID} onBack={vi.fn()} />);
    await userEvent.type(await screen.findByLabelText(/Value/), "750000.00");
    await userEvent.click(
      screen.getByRole("button", { name: "Record appraisal" }),
    );

    expect(
      await screen.findByText("Appraised value recorded."),
    ).toBeInTheDocument();
    const body: unknown = await (recorded as Request).json();
    expect(body).toMatchObject({ value: "750000.00" });
    expect(fetchMock).toHaveBeenCalledWith(
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("hides the appraisal form for Instruments valued another way", async () => {
    stubRoutes(routes());

    render(<PositionDetail id={ID} onBack={vi.fn()} />);
    await screen.findByText("Market-priced");

    expect(
      screen.queryByRole("button", { name: "Record appraisal" }),
    ).not.toBeInTheDocument();
  });
});
