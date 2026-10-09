import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { respond, stubRoutes } from "../test/fetchRoutes";
import { BenchmarkSettings } from "./BenchmarkSettings";

const available = [
  { key: "nifty50_tri", name: "NIFTY 50 TRI", kind: "index" },
  { key: "cpi", name: "CPI (Inflation)", kind: "inflation" },
];

const config = {
  available,
  asset_classes: [
    {
      asset_class: "equity",
      assigned_key: "nifty50_tri",
      default_key: "nifty50_tri",
      overridden: false,
    },
    {
      asset_class: "debt",
      assigned_key: "cpi",
      default_key: "cpi",
      overridden: false,
    },
  ],
};

describe("BenchmarkSettings", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows each asset class with its assigned and default Benchmark", async () => {
    stubRoutes({
      "GET /api/benchmarks/config": () => respond(200, config),
      "GET /api/benchmarks/instruments": () => respond(200, []),
    });

    render(<BenchmarkSettings />);

    const equity = await screen.findByText(/Equity — NIFTY 50 TRI/);
    expect(equity).toBeInTheDocument();
    expect(screen.getByText(/Debt — CPI \(Inflation\)/)).toBeInTheDocument();
  });

  it("saves a changed asset-class Benchmark", async () => {
    let saved = false;
    stubRoutes({
      "GET /api/benchmarks/config": () => respond(200, config),
      "GET /api/benchmarks/instruments": () => respond(200, []),
      "PUT /api/benchmarks/config/equity": () => {
        saved = true;
        return respond(200, {
          asset_class: "equity",
          assigned_key: "cpi",
          default_key: "nifty50_tri",
          overridden: true,
        });
      },
    });

    render(<BenchmarkSettings />);

    const pickers = await screen.findAllByLabelText("Benchmark", {
      selector: "select",
    });
    await userEvent.selectOptions(pickers[0] as HTMLSelectElement, "cpi");

    expect(saved).toBe(true);
    expect(await screen.findByText(/Equity — CPI/)).toBeInTheDocument();
  });

  it("lists Instruments with their resolved Benchmark for override", async () => {
    stubRoutes({
      "GET /api/benchmarks/config": () => respond(200, config),
      "GET /api/benchmarks/instruments": () =>
        respond(200, [
          {
            instrument_id: "7f1d6f8e-35a4-4c55-9df2-6f0f6b0c1a11",
            name: "HDFC Top 200 Fund",
            asset_class: "equity",
            resolved_key: "nifty50_tri",
            resolved_name: "NIFTY 50 TRI",
            override_key: null,
          },
        ]),
    });

    render(<BenchmarkSettings />);

    expect(
      await screen.findByText("Per-Instrument overrides"),
    ).toBeInTheDocument();
    expect(screen.getByText("HDFC Top 200 Fund")).toBeInTheDocument();
    expect(
      screen.getByRole("option", { name: "Use Equity — NIFTY 50 TRI" }),
    ).toBeInTheDocument();
  });

  it("says so when the settings can't be loaded", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.reject(new TypeError("Failed to fetch"))),
    );

    render(<BenchmarkSettings />);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Couldn't reach the Wealth Tracker server.",
    );
  });
});
