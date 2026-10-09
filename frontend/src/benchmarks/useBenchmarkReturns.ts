import { useEffect, useState } from "react";

import { loadBenchmarkReturns, type BenchmarkPoint } from "./benchmarkReturns";

export type OverlayState =
  | { kind: "loading" }
  | { kind: "unavailable" }
  | { kind: "ready"; points: BenchmarkPoint[] };

export function useBenchmarkReturns(
  benchmark: string,
  from: string,
  to: string,
): OverlayState {
  const [state, setState] = useState<OverlayState>({ kind: "loading" });

  useEffect(() => {
    let current = true;
    void loadBenchmarkReturns(benchmark, from, to).then((result) => {
      if (current) {
        setState(toOverlayState(result));
      }
    });
    return () => {
      current = false;
    };
  }, [benchmark, from, to]);

  return state;
}

type ReturnsResult = Awaited<ReturnType<typeof loadBenchmarkReturns>>;

function toOverlayState(result: ReturnsResult): OverlayState {
  return result.kind === "ok"
    ? { kind: "ready", points: result.series.points }
    : { kind: "unavailable" };
}
