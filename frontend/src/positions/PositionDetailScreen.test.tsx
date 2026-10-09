import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { respond, stubRoutes } from "../test/fetchRoutes";
import { PositionDetailScreen } from "./PositionDetailScreen";

const POSITION_ID = "7f1d6f8e-35a4-4c55-9df2-6f0f6b0c1a11";

const detail = {
  id: POSITION_ID,
  scheme: "HDFC Top 200 Fund - Direct Plan - Growth",
  institution: "HDFC Mutual Fund",
  folio: "1234567890",
  units: "1830.270",
  cost_basis: "129871.58",
  instrument_kind: "mutual_fund",
  allowed_types: ["purchase", "redemption", "sip"],
  allowed_income_types: ["dividend", "idcw", "interest", "rent"],
  reinvestable: true,
  income: [],
  income_total: "0",
  cash_flow_total: "0",
  transactions: [
    {
      date: "2024-05-10",
      kind: "PURCHASE",
      description: "Purchase",
      units: "1830.270",
      amount: "129871.58",
      notes: null,
      synthetic: false,
    },
  ],
};

function routes(
  overrides: Record<
    string,
    (request: Request) => Response | Promise<Response>
  > = {},
) {
  return {
    [`GET /api/positions/${POSITION_ID}`]: () => respond(200, detail),
    ...overrides,
  };
}

interface FormValues {
  type?: string;
  date: string;
  units: string;
  amount: string;
}

async function fillForm({ type, date, units, amount }: FormValues) {
  if (type !== undefined) {
    await userEvent.selectOptions(await screen.findByLabelText("Type"), type);
  }
  await userEvent.type(await screen.findByLabelText("Date"), date);
  await userEvent.type(await screen.findByLabelText("Units"), units);
  await userEvent.type(await screen.findByLabelText("Cost (₹)"), amount);
}

describe("PositionDetailScreen", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("offers only the Instrument's allowed Transaction types", async () => {
    stubRoutes(routes());

    render(<PositionDetailScreen positionId={POSITION_ID} onBack={vi.fn()} />);

    const select = await screen.findByLabelText("Type");
    expect(
      within(select)
        .getAllByRole("option")
        .map((o) => o.textContent),
    ).toEqual(["Purchase", "Redemption", "SIP"]);
    expect(select).toHaveValue("purchase");
  });

  it("adds a Transaction and shows the updated units and cost basis", async () => {
    const updated = {
      ...detail,
      units: "1930.270",
      cost_basis: "139871.58",
      transactions: [
        ...detail.transactions,
        {
          date: "2026-09-01",
          kind: "PURCHASE",
          description: "Manual purchase",
          units: "100.000",
          amount: "10000.00",
          notes: "top-up",
          synthetic: false,
        },
      ],
    };
    stubRoutes(
      routes({
        [`POST /api/positions/${POSITION_ID}/transactions`]: () =>
          respond(201, updated),
      }),
    );

    render(<PositionDetailScreen positionId={POSITION_ID} onBack={vi.fn()} />);
    await fillForm({
      date: "2026-09-01",
      units: "100.000",
      amount: "10000.00",
    });
    await userEvent.click(
      screen.getByRole("button", { name: "Add Transaction" }),
    );

    expect(await screen.findByText(/Units 1,930.270/)).toBeInTheDocument();
    expect(screen.getByText(/Cost basis ₹1,39,871.58/)).toBeInTheDocument();
    expect(screen.getByText("top-up")).toBeInTheDocument();
  });

  it("shows the server's message when the type is invalid", async () => {
    stubRoutes(
      routes({
        [`POST /api/positions/${POSITION_ID}/transactions`]: () =>
          respond(400, {
            code: "unexpected_type",
            message:
              "A mutual_fund Position doesn't accept a contribution Transaction.",
          }),
      }),
    );

    render(<PositionDetailScreen positionId={POSITION_ID} onBack={vi.fn()} />);
    await fillForm({
      type: "purchase",
      date: "2026-09-01",
      units: "10.000",
      amount: "1000.00",
    });
    await userEvent.click(
      screen.getByRole("button", { name: "Add Transaction" }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "doesn't accept",
    );
  });

  it("refuses a date in the future before calling the server", async () => {
    const post = vi.fn(() => respond(201, detail));
    stubRoutes(
      routes({ [`POST /api/positions/${POSITION_ID}/transactions`]: post }),
    );

    render(<PositionDetailScreen positionId={POSITION_ID} onBack={vi.fn()} />);
    await fillForm({
      type: "purchase",
      date: "2999-01-01",
      units: "10.000",
      amount: "1000.00",
    });
    await userEvent.click(
      screen.getByRole("button", { name: "Add Transaction" }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent("future");
    expect(post).not.toHaveBeenCalled();
  });

  it("records a withdrawn dividend as Cash Flow without changing units", async () => {
    const updated = {
      ...detail,
      income: [
        {
          date: "2026-09-01",
          kind: "dividend",
          gross_amount: "1000.00",
          tax_deducted: "100.00",
          net_amount: "900.00",
          withdrawn: true,
          units: null,
        },
      ],
      income_total: "900.00",
      cash_flow_total: "900.00",
    };
    stubRoutes(
      routes({
        [`POST /api/positions/${POSITION_ID}/income`]: () =>
          respond(201, updated),
      }),
    );

    render(<PositionDetailScreen positionId={POSITION_ID} onBack={vi.fn()} />);
    await userEvent.selectOptions(
      await screen.findByLabelText("Income type"),
      "dividend",
    );
    await userEvent.selectOptions(
      screen.getByLabelText("Disposition"),
      "withdrawn",
    );
    await userEvent.type(screen.getByLabelText("Income date"), "2026-09-01");
    await userEvent.type(screen.getByLabelText("Gross amount (₹)"), "1000.00");
    await userEvent.type(screen.getByLabelText(/Tax deducted/), "100.00");
    await userEvent.click(screen.getByRole("button", { name: "Add Income" }));

    expect(
      await screen.findByText("Withdrawn (Cash Flow)"),
    ).toBeInTheDocument();
    expect(screen.getAllByText("₹900.00")).toHaveLength(2);
    expect(screen.getByText(/Units 1,830.270/)).toBeInTheDocument();
  });

  it("reinvests a dividend by sending the NAV and showing the raised quantity", async () => {
    const updated = {
      ...detail,
      units: "1860.270",
      cost_basis: "130771.58",
      income: [
        {
          date: "2026-09-01",
          kind: "dividend",
          gross_amount: "1000.00",
          tax_deducted: "100.00",
          net_amount: "900.00",
          withdrawn: false,
          units: "30.000",
        },
      ],
      income_total: "900.00",
      cash_flow_total: "0",
    };
    const bodies: unknown[] = [];
    stubRoutes(
      routes({
        [`POST /api/positions/${POSITION_ID}/income`]: async (
          request: Request,
        ) => {
          bodies.push(await request.json());
          return respond(201, updated);
        },
      }),
    );

    render(<PositionDetailScreen positionId={POSITION_ID} onBack={vi.fn()} />);
    await userEvent.type(
      await screen.findByLabelText("Income date"),
      "2026-09-01",
    );
    await userEvent.type(screen.getByLabelText("Gross amount (₹)"), "1000.00");
    await userEvent.type(screen.getByLabelText(/Tax deducted/), "100.00");
    await userEvent.type(
      screen.getByLabelText("Reinvestment NAV (₹)"),
      "30.00",
    );
    await userEvent.click(screen.getByRole("button", { name: "Add Income" }));

    expect(bodies[0]).toMatchObject({
      type: "dividend",
      reinvested: true,
      nav: "30.00",
    });
    expect(await screen.findByText(/Units 1,860.270/)).toBeInTheDocument();
  });

  it("only offers Withdraw when the Instrument cannot hold units", async () => {
    stubRoutes(
      routes({
        [`GET /api/positions/${POSITION_ID}`]: () =>
          respond(200, {
            ...detail,
            instrument_kind: "fd",
            reinvestable: false,
          }),
      }),
    );

    render(<PositionDetailScreen positionId={POSITION_ID} onBack={vi.fn()} />);

    const disposition = await screen.findByLabelText("Disposition");
    expect(disposition).toHaveValue("withdrawn");
    expect(within(disposition).getAllByRole("option")).toHaveLength(1);
    expect(within(disposition).getByRole("option")).toHaveTextContent(
      "Withdraw",
    );
  });
});
