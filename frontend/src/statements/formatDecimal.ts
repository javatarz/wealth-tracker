const indianGrouping = new Intl.NumberFormat("en-IN");

/** Formats a decimal string with Indian digit grouping, keeping every printed digit. */
export function formatDecimal(value: string | null): string {
  if (value === null) {
    return "—";
  }
  const match = /^([+-]?)(\d+)(?:\.(\d+))?$/.exec(value);
  const integer = match?.[2];
  if (match === null || integer === undefined) {
    return value;
  }
  const sign = match[1] === "-" ? "−" : "";
  const fraction = match[3] === undefined ? "" : `.${match[3]}`;
  return `${sign}${indianGrouping.format(BigInt(integer))}${fraction}`;
}
