import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { respond, stubRoutes } from "../test/fetchRoutes";
import { Dashboard } from "./Dashboard";

const equity = {
  id: "7f1d6f8e-35a4-4c55-9df2-6f0f6b0c1a11",
  scheme: "HDFC Top 200 Fund - Direct Plan - Growth",
  account: "HDFC Mutual Fund · 1234567890",
  asset_class: "equity",
  units: "1830.270",
  cost_basis: "129871.58",
  current_value: "129476.23",
  percent: "35.46",
};

const other = {
  id: "4d7b135c-cb57-4c60-adf5-623032f290f0",
  scheme: "ICICI Prudential Value Discovery Fund - Direct - Growth",
  account: "ICICI Prudential Mutual Fund · 1234567890",
  asset_class: "other",
  units: "3260.204",
  cost_basis: "156266.13",
  current_value: "188101.71",
  percent: "51.51",
};

const series = [
  { date: "2024-04-01", value: "300000.00" },
  { date: "2025-03-31", value: "365170.11" },
];

const filters = {
  members: [{ id: "b3785e8f-16fa-4e81-814c-48b39fa3a85f", name: "Me" }],
  asset_classes: [
    { value: "equity", label: "Equity" },
    { value: "other", label: "Other" },
  ],
};

const emptyDashboard = {
  current_value: "0",
  invested: "0",
  absolute_return: "0",
  series: [],
  positions: [],
};

function dashboard(overrides: Record<string, unknown>) {
  return {
    current_value: "317577.94",
    invested: "286137.71",
    absolute_return: "31440.23",
    series,
    positions: [equity, other],
    ...overrides,
  };
}

function stub(dashboardBody: unknown) {
  return stubRoutes({
    "GET /api/dashboard": () => respond(200, dashboardBody),
    "GET /api/filters": () => respond(200, filters),
  });
}

describe("Dashboard", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("draws the Net Worth graph and lists each Position's share", async () => {
    stub(dashboard({}));

    render(<Dashboard onOpenPosition={vi.fn()} />);

    expect(
      await screen.findByRole("img", { name: "Net Worth over time" }),
    ).toBeInTheDocument();
    const row = screen.getByRole("row", { name: /HDFC Top 200 Fund/ });
    expect(within(row).getByText("35.46%")).toBeInTheDocument();
  });

  it("shows the returns summary", async () => {
    stub(dashboard({}));

    render(<Dashboard onOpenPosition={vi.fn()} />);

    const returns = await screen.findByRole("region", { name: "Returns" });
    expect(within(returns).getByText("3,17,577.94")).toBeInTheDocument();
    expect(within(returns).getByText("31,440.23")).toBeInTheDocument();
  });

  it("rescopes the dashboard when the Asset Class filter changes", async () => {
    const fetchMock = stubRoutes({
      "GET /api/dashboard": (request) => {
        const scoped =
          new URL(request.url).searchParams.get("asset_class") === "equity";
        return respond(
          200,
          dashboard({ positions: scoped ? [equity] : [equity, other] }),
        );
      },
      "GET /api/filters": () => respond(200, filters),
    });

    render(<Dashboard onOpenPosition={vi.fn()} />);
    await screen.findByText(/ICICI Prudential Value/);

    await userEvent.selectOptions(
      screen.getByLabelText("Asset Class"),
      "equity",
    );

    await waitFor(() => {
      expect(
        screen.queryByText(/ICICI Prudential Value/),
      ).not.toBeInTheDocument();
    });
    expect(screen.getByText(/HDFC Top 200/)).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalled();
  });

  it("opens a Position when its row is clicked", async () => {
    stub(dashboard({}));
    const onOpenPosition = vi.fn();

    render(<Dashboard onOpenPosition={onOpenPosition} />);
    await userEvent.click(
      await screen.findByRole("row", { name: /HDFC Top 200 Fund/ }),
    );

    expect(onOpenPosition).toHaveBeenCalledWith(equity);
  });

  it("shows an empty state when there are no Positions", async () => {
    stub(emptyDashboard);

    render(<Dashboard onOpenPosition={vi.fn()} />);

    expect(
      await screen.findByText(/No Positions match this view/),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("region", { name: "Returns" }),
    ).not.toBeInTheDocument();
  });
});
