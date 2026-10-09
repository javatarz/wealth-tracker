import { api } from "../api/client";
import type { components } from "../api/schema";

export type BenchmarkPoint = components["schemas"]["BenchmarkPointOut"];
export type BenchmarkSeries = components["schemas"]["BenchmarkReturnOut"];

export type ReturnsResult =
  { kind: "ok"; series: BenchmarkSeries } | { kind: "error"; message: string };

const UNREACHABLE = "Couldn't reach the Wealth Tracker server.";
const NO_HISTORY = "No price history for that Benchmark yet.";

export async function loadBenchmarkReturns(
  benchmark: string,
  from: string,
  to: string,
): Promise<ReturnsResult> {
  try {
    return toResult(await fetchReturns(benchmark, from, to));
  } catch {
    return { kind: "error", message: UNREACHABLE };
  }
}

function fetchReturns(benchmark: string, from: string, to: string) {
  return api.GET("/api/benchmarks/returns", {
    params: { query: { benchmark, from, to } },
  });
}

function toResult({
  data,
}: Awaited<ReturnType<typeof fetchReturns>>): ReturnsResult {
  return data
    ? { kind: "ok", series: data }
    : { kind: "error", message: NO_HISTORY };
}
