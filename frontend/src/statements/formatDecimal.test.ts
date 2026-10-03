import { describe, expect, it } from "vitest";

import { formatDecimal } from "./formatDecimal";

describe("formatDecimal", () => {
  it.each([
    ["129476.23", "1,29,476.23"],
    ["-76739.54", "−76,739.54"],
    ["1830.270", "1,830.270"],
    ["0", "0"],
    ["12345678901234567890.5", "1,23,45,67,89,01,23,45,67,890.5"],
  ])("formats %s as %s", (input, expected) => {
    expect(formatDecimal(input)).toBe(expected);
  });

  it("renders null as a dash", () => {
    expect(formatDecimal(null)).toBe("—");
  });

  it("passes unexpected input through unchanged", () => {
    expect(formatDecimal("1e5")).toBe("1e5");
  });
});
