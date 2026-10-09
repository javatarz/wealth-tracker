/** Human labels for the Transaction types the API accepts, keyed by type. */
const LABELS: Record<string, string> = {
  purchase: "Purchase",
  redemption: "Redemption",
  sip: "SIP",
  contribution: "Contribution",
  maturity: "Maturity",
};

export function transactionTypeLabel(type: string): string {
  return LABELS[type] ?? type;
}
