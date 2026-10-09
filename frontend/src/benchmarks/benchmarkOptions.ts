import type { BenchmarkDefinition } from "./benchmarkConfig";

export const CLASS_LABELS: Record<string, string> = {
  equity: "Equity",
  debt: "Debt",
  gold: "Gold",
  real_estate: "Real estate",
  crypto: "Crypto",
  cash: "Cash",
  other: "Other",
};

export function classLabel(assetClass: string): string {
  return CLASS_LABELS[assetClass] ?? assetClass;
}

export function nameOf(available: BenchmarkDefinition[], key: string): string {
  return available.find((definition) => definition.key === key)?.name ?? key;
}
