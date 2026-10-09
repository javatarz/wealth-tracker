import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { respond, stubRoutes } from "../test/fetchRoutes";
import { BenchmarkOverlay } from "./BenchmarkOverlay";

const series = {
  key: "nifty50_tri",
  name: "NIFTY 50 TRI",
  start: "2024-01-01",
  end: "2024-01-31",
  points: [
    { date: "2024-01-01", value: "100" },
    { date: "2024-01-31", value: "110" },
  ],
};

describe("BenchmarkOverlay", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("draws the Benchmark line over the requested range", async () => {
    stubRoutes({
      "GET /api/benchmarks/returns": () => respond(200, series),
    });

    render(
      <BenchmarkOverlay
        benchmark="nifty50_tri"
        name="NIFTY 50 TRI"
        from="2024-01-01"
        to="2024-01-31"
      />,
    );

    const chart = await screen.findByRole("img", {
      name: "Growth with benchmark overlay",
    });
    expect(chart.querySelector("path")).toHaveAttribute(
      "d",
      "L 24 216 L 696 24",
    );
    expect(screen.getByText("NIFTY 50 TRI")).toBeInTheDocument();
  });

  it("hides and shows the line with the overlay toggle", async () => {
    stubRoutes({
      "GET /api/benchmarks/returns": () => respond(200, series),
    });

    render(
      <BenchmarkOverlay
        benchmark="nifty50_tri"
        name="NIFTY 50 TRI"
        from="2024-01-01"
        to="2024-01-31"
      />,
    );

    await userEvent.click(
      screen.getByRole("checkbox", { name: "Show benchmark line" }),
    );
    expect(
      screen.queryByRole("img", { name: "Growth with benchmark overlay" }),
    ).not.toBeInTheDocument();

    await userEvent.click(
      screen.getByRole("checkbox", { name: "Show benchmark line" }),
    );
    expect(
      await screen.findByRole("img", { name: "Growth with benchmark overlay" }),
    ).toBeInTheDocument();
  });

  it("explains when the Benchmark has no price history yet", async () => {
    stubRoutes({
      "GET /api/benchmarks/returns": () =>
        respond(404, { detail: "no prices" }),
    });

    render(
      <BenchmarkOverlay
        benchmark="cpi"
        name="CPI (Inflation)"
        from="2024-01-01"
        to="2024-01-31"
      />,
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "No price history for CPI (Inflation) yet.",
    );
  });
});
