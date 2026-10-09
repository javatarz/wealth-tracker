/** Human labels for the Income types and dispositions the API accepts. */
const TYPES: Record<string, string> = {
  dividend: "Dividend",
  idcw: "IDCW",
  interest: "Interest",
  rent: "Rent",
};

const DISPOSITIONS: Record<string, string> = {
  reinvested: "Reinvest",
  withdrawn: "Withdraw",
};

export function incomeTypeLabel(type: string): string {
  return TYPES[type] ?? type;
}

export function dispositionLabel(disposition: string): string {
  return DISPOSITIONS[disposition] ?? disposition;
}

/** Only quantity-bearing Positions can reinvest; the rest can only withdraw. */
export function dispositionsFor(reinvestable: boolean): string[] {
  return reinvestable ? ["reinvested", "withdrawn"] : ["withdrawn"];
}
