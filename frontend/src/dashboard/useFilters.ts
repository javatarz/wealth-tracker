import { useEffect, useState } from "react";

import { getFilters, type FilterOptions } from "./dashboardApi";

/** What the Asset Class dropdown shows until (or if) the server answers. */
export const ASSET_CLASSES: { value: string; label: string }[] = [
  { value: "equity", label: "Equity" },
  { value: "debt", label: "Debt" },
  { value: "gold", label: "Gold" },
  { value: "real_estate", label: "Real Estate" },
  { value: "cash", label: "Cash" },
  { value: "crypto", label: "Crypto" },
  { value: "other", label: "Other" },
];

const FALLBACK: FilterOptions = { members: [], asset_classes: ASSET_CLASSES };

export type FiltersState = FilterOptions;

export function useFilters(): FiltersState {
  const [filters, setFilters] = useState<FiltersState>(FALLBACK);

  useEffect(() => {
    void getFilters().then((result) => {
      setFilters(result.kind === "ok" ? result.filters : FALLBACK);
    });
  }, []);

  return filters;
}
