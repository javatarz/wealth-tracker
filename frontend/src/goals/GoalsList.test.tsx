import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { respond, stubRoutes } from "../test/fetchRoutes";
import { GoalsList } from "./GoalsList";

const account = {
  id: "0b3c4f9a-8d2e-4c71-a5b6-1e2f3a4b5c6d",
  institution: "HDFC Mutual Fund",
  name: "HDFC Mutual Fund · 1234567890",
};

const goal = {
  id: "7f1d6f8e-35a4-4c55-9df2-6f0f6b0c1a11",
  name: "New Car",
  target_amount: "200000.00",
  target_date: "2027-01-01",
  account_ids: [account.id],
  current_value: "120000.00",
  percent_funded: "60.00",
};

describe("GoalsList", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows each Goal's progress against its target", async () => {
    stubRoutes({
      "GET /api/goals": () => respond(200, [goal]),
      "GET /api/accounts": () => respond(200, [account]),
    });

    render(<GoalsList />);

    const card = await screen.findByRole("article");
    expect(
      within(card).getByRole("heading", { name: "New Car" }),
    ).toBeInTheDocument();
    expect(card).toHaveTextContent("₹1,20,000.00 of ₹2,00,000.00 · 60.00%");
    expect(
      within(card).getByRole<HTMLProgressElement>("progressbar").value,
    ).toBe(60);
  });

  it("says so when there are no Goals yet", async () => {
    stubRoutes({
      "GET /api/goals": () => respond(200, []),
      "GET /api/accounts": () => respond(200, []),
    });

    render(<GoalsList />);

    expect(await screen.findByText(/No Goals yet/)).toBeInTheDocument();
  });

  it("creates a Goal and assigns a funding Account", async () => {
    let posted: unknown = null;
    stubRoutes({
      "GET /api/goals": () => respond(200, posted ? [goal] : []),
      "GET /api/accounts": () => respond(200, [account]),
      "POST /api/goals": async (request) => {
        posted = await request.json();
        return respond(201, goal);
      },
    });
    render(<GoalsList />);

    await userEvent.click(
      await screen.findByRole("button", { name: "New Goal" }),
    );
    await userEvent.type(screen.getByLabelText("Goal name"), "New Car");
    await userEvent.type(screen.getByLabelText("Target amount (₹)"), "200000");
    await userEvent.type(screen.getByLabelText("Target date"), "2027-01-01");
    await userEvent.click(screen.getByLabelText(account.name));
    await userEvent.click(screen.getByRole("button", { name: "Create Goal" }));

    expect(
      await screen.findByRole("heading", { name: "New Car" }),
    ).toBeInTheDocument();
    expect(posted).toEqual({
      name: "New Car",
      target_amount: "200000",
      target_date: "2027-01-01",
      account_ids: [account.id],
    });
  });

  it("edits an existing Goal", async () => {
    let updated: unknown = null;
    const renamed = { ...goal, name: "Family Car" };
    stubRoutes({
      "GET /api/goals": () => respond(200, [updated ? renamed : goal]),
      "GET /api/accounts": () => respond(200, [account]),
      [`PUT /api/goals/${goal.id}`]: async (request) => {
        updated = await request.json();
        return respond(200, renamed);
      },
    });
    render(<GoalsList />);

    await userEvent.click(await screen.findByRole("button", { name: "Edit" }));
    const name = screen.getByLabelText("Goal name");
    await userEvent.clear(name);
    await userEvent.type(name, "Family Car");
    await userEvent.click(screen.getByRole("button", { name: "Save changes" }));

    expect(
      await screen.findByRole("heading", { name: "Family Car" }),
    ).toBeInTheDocument();
    expect(updated).toMatchObject({ name: "Family Car" });
  });

  it("deletes a Goal", async () => {
    let deleted = false;
    stubRoutes({
      "GET /api/goals": () => respond(200, deleted ? [] : [goal]),
      "GET /api/accounts": () => respond(200, [account]),
      [`DELETE /api/goals/${goal.id}`]: () => {
        deleted = true;
        return respond(204, null);
      },
    });
    render(<GoalsList />);

    await userEvent.click(
      await screen.findByRole("button", { name: "Delete" }),
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Confirm delete" }),
    );

    expect(await screen.findByText(/No Goals yet/)).toBeInTheDocument();
  });

  it("keeps a Goal when the delete is not confirmed", async () => {
    stubRoutes({
      "GET /api/goals": () => respond(200, [goal]),
      "GET /api/accounts": () => respond(200, [account]),
    });
    render(<GoalsList />);

    await userEvent.click(
      await screen.findByRole("button", { name: "Delete" }),
    );
    await userEvent.click(screen.getByRole("button", { name: "Keep" }));

    expect(
      screen.getByRole("heading", { name: "New Car" }),
    ).toBeInTheDocument();
  });

  it("says so when the server can't be reached", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.reject(new TypeError("Failed to fetch"))),
    );

    render(<GoalsList />);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Couldn't reach the Wealth Tracker server.",
    );
  });
});
