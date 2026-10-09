import { describe, expect, it } from "vitest";

import { overlayGeometry, VIEW_BOX, type OverlayLine } from "./overlayGeometry";

const line = (key: string, values: [string, string][]): OverlayLine => ({
  key,
  name: key,
  points: values.map(([date, value]) => ({ date, value })),
});

describe("overlayGeometry", () => {
  it("returns nothing when there are no points", () => {
    expect(overlayGeometry([line("nifty50_tri", [])])).toEqual([]);
  });

  it("gives every line one path on a shared domain", () => {
    const geometry = overlayGeometry([
      line("nifty50_tri", [
        ["2024-01-01", "100"],
        ["2024-01-31", "110"],
      ]),
      line("cpi", [
        ["2024-01-01", "50"],
        ["2024-01-31", "60"],
      ]),
    ]);

    expect(geometry.map((entry) => entry.key)).toEqual(["nifty50_tri", "cpi"]);
    for (const entry of geometry) {
      expect(entry.path).toMatch(/^L [\d.]+ [\d.]+( L [\d.]+ [\d.]+)+$/);
    }
  });

  it("starts and ends the first point at the plot padding", () => {
    const [geometry] = overlayGeometry([
      line("nifty50_tri", [
        ["2024-01-01", "100"],
        ["2024-01-31", "200"],
      ]),
    ]);

    expect(geometry?.path.split(" ").slice(1, 3)).toEqual(["24", "216"]);
    expect(geometry?.path.split(" ").slice(-2)).toEqual(["696", "24"]);
  });

  it("pins a flat series to the top of the plot rather than dividing by zero", () => {
    const [geometry] = overlayGeometry([
      line("cpi", [
        ["2024-01-01", "100"],
        ["2024-01-31", "100"],
      ]),
    ]);

    expect(geometry?.path).toBe("L 24 216 L 696 216");
  });

  it("exposes a viewBox matching the coordinate space", () => {
    expect(VIEW_BOX).toBe("0 0 720 240");
  });
});
