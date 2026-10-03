const indianGrouping = new Intl.NumberFormat("en-IN");
const DECIMAL = /^([+-]?)(\d+)(?:\.(\d+))?$/;
const MISSING = "—";
const MINUS = "−";

/** Formats a decimal string with Indian digit grouping, keeping every printed digit. */
export function formatDecimal(value: string | null): string {
  if (value === null) {
    return MISSING;
  }
  const match = DECIMAL.exec(value);
  return match ? groupDigits(match) : value;
}

function groupDigits([, sign, integer = "0", fraction]: RegExpExecArray) {
  const signText = sign === "-" ? MINUS : "";
  const fractionText = fraction === undefined ? "" : `.${fraction}`;
  return `${signText}${indianGrouping.format(BigInt(integer))}${fractionText}`;
}
