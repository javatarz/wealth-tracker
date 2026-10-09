import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { respond, stubRoutes } from "../test/fetchRoutes";
import { GoalForm } from "./GoalForm";

const account = {
  id: "0b3c4f9a-8d2e-4c71-a5b6-1e2f3a4b5c6d",
  institution: "HDFC Mutual Fund",
  name: "HDFC Mutual Fund · 1234567890",
};

describe("GoalForm projection strategy", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("sends the CAGR rate when the CAGR strategy is chosen", async () => {
    let posted: unknown = null;
    stubRoutes({
      "POST /api/goals": async (request) => {
        posted = await request.json();
        return respond(201, {});
      },
    });
    render(
      <GoalForm
        accounts={[account]}
        onSaved={() => undefined}
        onCancel={() => undefined}
      />,
    );

    await userEvent.type(screen.getByLabelText("Goal name"), "New Car");
    await userEvent.type(screen.getByLabelText("Target amount (₹)"), "200000");
    await userEvent.type(screen.getByLabelText("Target date"), "2027-01-01");
    await userEvent.selectOptions(
      screen.getByLabelText("Projection strategy"),
      "cagr",
    );
    await userEvent.type(
      screen.getByLabelText("CAGR rate (e.g. 0.12)"),
      "0.12",
    );
    await userEvent.click(screen.getByRole("button", { name: "Create Goal" }));

    expect(posted).toEqual({
      name: "New Car",
      target_amount: "200000",
      target_date: "2027-01-01",
      account_ids: [],
      projection_strategy: "cagr",
      cagr_rate: "0.12",
      trailing_window_years: null,
    });
  });

  it("sends the window when the trailing-window strategy is chosen", async () => {
    let posted: unknown = null;
    stubRoutes({
      "POST /api/goals": async (request) => {
        posted = await request.json();
        return respond(201, {});
      },
    });
    render(
      <GoalForm
        accounts={[account]}
        onSaved={() => undefined}
        onCancel={() => undefined}
      />,
    );

    await userEvent.type(screen.getByLabelText("Goal name"), "New Car");
    await userEvent.type(screen.getByLabelText("Target amount (₹)"), "200000");
    await userEvent.type(screen.getByLabelText("Target date"), "2027-01-01");
    await userEvent.selectOptions(
      screen.getByLabelText("Projection strategy"),
      "trailing_window",
    );
    await userEvent.type(screen.getByLabelText("Window (years)"), "3");
    await userEvent.click(screen.getByRole("button", { name: "Create Goal" }));

    expect(posted).toMatchObject({
      projection_strategy: "trailing_window",
      cagr_rate: null,
      trailing_window_years: 3,
    });
  });
});
