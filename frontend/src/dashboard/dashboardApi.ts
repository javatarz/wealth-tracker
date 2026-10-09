import { api } from "../api/client";
import type { components, operations } from "../api/schema";

export type DashboardSummary = components["schemas"]["DashboardSummary"];
export type DashboardPosition = components["schemas"]["DashboardPosition"];
export type NetWorthPoint = components["schemas"]["NetWorthPoint"];
export type FilterOptions = components["schemas"]["FilterOptions"];

type DashboardQuery = NonNullable<
  operations["getDashboard"]["parameters"]["query"]
>;
export type AssetClass = NonNullable<DashboardQuery["asset_class"]>;

export interface Scope {
  member: string;
  /** One of the Asset Class dropdown values, or `ALL`. */
  assetClass: string;
}

export const ALL = "";

export type DashboardResult =
  | { kind: "ok"; dashboard: DashboardSummary }
  | { kind: "error"; message: string };

const FAILED: DashboardResult = {
  kind: "error",
  message: "Couldn't load your Net Worth.",
};
const UNREACHABLE: DashboardResult = {
  kind: "error",
  message: "Couldn't reach the Wealth Tracker server.",
};

function query(scope: Scope): DashboardQuery {
  return {
    member: scope.member === ALL ? null : scope.member,
    asset_class:
      scope.assetClass === ALL ? null : (scope.assetClass as AssetClass),
  };
}

export async function getDashboard(scope: Scope): Promise<DashboardResult> {
  try {
    const { data } = await api.GET("/api/dashboard", {
      params: { query: query(scope) },
    });
    return data ? { kind: "ok", dashboard: data } : FAILED;
  } catch {
    return UNREACHABLE;
  }
}

export type FiltersResult =
  { kind: "ok"; filters: FilterOptions } | { kind: "error"; message: string };

const FILTERS_FAILED: FiltersResult = {
  kind: "error",
  message: "Couldn't load the filter options.",
};
const FILTERS_UNREACHABLE: FiltersResult = {
  kind: "error",
  message: "Couldn't reach the Wealth Tracker server.",
};

export async function getFilters(): Promise<FiltersResult> {
  try {
    const { data } = await api.GET("/api/filters");
    return data ? { kind: "ok", filters: data } : FILTERS_FAILED;
  } catch {
    return FILTERS_UNREACHABLE;
  }
}
