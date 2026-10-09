import { render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { respond, stubRoutes } from "../test/fetchRoutes";
import { GoalCards } from "./GoalCards";

const goal = {
  id: "7f1d6f8e-35a4-4c55-9df2-6f0f6b0c1a11",
  name: "New Car",
  target_amount: "200000.00",
  target_date: "2027-01-01",
  account_ids: [],
  current_value: "120000.00",
  percent_funded: "60.00",
  projection_strategy: "cagr",
  cagr_rate: "0.12",
  trailing_window_years: null,
};

const projection = {
  goal_id: goal.id,
  strategy: "cagr",
  rate: "0.12",
  current_value: "120000.00",
  target_amount: "200000.00",
  target_date: "2027-01-01",
  projected_value: "134400.00",
  gap: "65600.00",
  status: "at_risk",
  as_of: "2026-01-01",
  trajectory: [
    { on: "2026-01-01", value: "120000.00" },
    { on: "2027-01-01", value: "134400.00" },
  ],
};

const schedules = {
  schedules: [
    {
      id: "0b3c4f9a-8d2e-4c71-a5b6-1e2f3a4b5c6d",
      position_id: "1c2d3e4f-5a6b-4c7d-8e9f-0a1b2c3d4e5f",
      position_name: "HDFC Mutual Fund · HDFC Top 200",
      description: "Monthly SIP",
      direction: "contribution",
      frequency: "monthly",
      amount: "1000.00",
      start_date: "2026-01-01",
      end_date: null,
      escalation_rate: "0.10",
    },
  ],
  positions: [],
};

describe("GoalCards projections", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows the projection graph, status badge and scheduled transactions", async () => {
    stubRoutes({
      [`GET /api/goals/${goal.id}/projection`]: () => respond(200, projection),
      [`GET /api/goals/${goal.id}/scheduled-transactions`]: () =>
        respond(200, schedules),
    });

    render(
      <GoalCards
        goals={[goal]}
        onEdit={() => undefined}
        onDelete={() => undefined}
      />,
    );

    const card = await screen.findByRole("article");
    expect(await within(card).findByText("At risk")).toBeInTheDocument();
    expect(
      within(card).getByRole("img", { name: /Projected 1,34,400.00/ }),
    ).toBeInTheDocument();
    expect(within(card).getByText(/Monthly SIP/)).toBeInTheDocument();
    expect(within(card).getByText(/escalating 0.10\/yr/)).toBeInTheDocument();
  });

  it("keeps the card usable when projection loading fails", async () => {
    stubRoutes({
      [`GET /api/goals/${goal.id}/projection`]: () =>
        Promise.reject(new TypeError("Failed to fetch")),
      [`GET /api/goals/${goal.id}/scheduled-transactions`]: () =>
        Promise.reject(new TypeError("Failed to fetch")),
    });

    render(
      <GoalCards
        goals={[goal]}
        onEdit={() => undefined}
        onDelete={() => undefined}
      />,
    );

    const card = await screen.findByRole("article");
    expect(within(card).queryByRole("img")).not.toBeInTheDocument();
    expect(
      within(card).getByRole("heading", { name: "New Car" }),
    ).toBeInTheDocument();
  });
});
