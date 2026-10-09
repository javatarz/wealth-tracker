import { api } from "../api/client";
import type { components, operations } from "../api/schema";

export type BenchmarkConfig = components["schemas"]["BenchmarkConfigOut"];
export type AssetClassBenchmark =
  components["schemas"]["AssetClassBenchmarkOut"];
export type BenchmarkDefinition =
  components["schemas"]["BenchmarkDefinitionOut"];
// The path parameter is a closed union; the response schema only says string.
export type AssetClass =
  operations["setBenchmark"]["parameters"]["path"]["asset_class"];

export type ConfigResult =
  { kind: "ok"; config: BenchmarkConfig } | { kind: "error"; message: string };

export type SaveResult =
  | { kind: "ok"; assetClass: AssetClassBenchmark }
  | { kind: "error"; message: string };

const UNREACHABLE = "Couldn't reach the Wealth Tracker server.";
const LOAD_FAILED = "Couldn't load the benchmark settings.";
const SAVE_REJECTED = "The benchmark change was rejected.";

export async function loadBenchmarkConfig(): Promise<ConfigResult> {
  try {
    const { data } = await api.GET("/api/benchmarks/config");
    return data ? { kind: "ok", config: data } : failed(LOAD_FAILED);
  } catch {
    return failed(UNREACHABLE);
  }
}

export async function saveAssetClassBenchmark(
  assetClass: string,
  benchmark: string,
): Promise<SaveResult> {
  try {
    const { data } = await api.PUT("/api/benchmarks/config/{asset_class}", {
      params: { path: { asset_class: assetClass as AssetClass } },
      body: { benchmark },
    });
    return data ? { kind: "ok", assetClass: data } : rejected();
  } catch {
    return rejected(UNREACHABLE);
  }
}

function failed(message: string): ConfigResult {
  return { kind: "error", message };
}

function rejected(message = SAVE_REJECTED): SaveResult {
  return { kind: "error", message };
}
